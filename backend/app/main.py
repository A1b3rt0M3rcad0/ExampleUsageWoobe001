from __future__ import annotations
from typing import Any
from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from .config import get_settings
from .data import MockCommerceData
from .db import Database
from .security import ADMIN_SESSION_KEY, authenticate_admin, require_admin, require_bearer
from .woobe import WoobeChatSurfaceClient, WoobeIntegrationError

class LoginRequest(BaseModel): email:str; password:str
class StoreChatRequest(BaseModel): client_id:str=Field(min_length=8,max_length=120)
class ReportCreateRequest(BaseModel):
    title:str=Field(min_length=3,max_length=160); period_label:str=Field(min_length=1,max_length=80); executive_summary:str=Field(min_length=10,max_length=5000); findings:list[str]=Field(min_length=1,max_length=30); recommendations:list[str]=Field(default_factory=list,max_length=30)

settings=get_settings(); db=Database(settings); db.initialize(); mock=MockCommerceData(settings.public_store_base_url); woobe=WoobeChatSurfaceClient(settings)
app=FastAPI(title='Mercury Commerce Example API',version='1.0.0')
app.add_middleware(SessionMiddleware,secret_key=settings.app_secret_key,session_cookie='mercury_admin_session',same_site='lax',https_only=settings.app_environment.lower()=='production')
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

@app.get('/health')
def health(): return {'status':'ok'}

@app.get('/api/store/categories')
def store_categories(): return {'categories':mock.categories}

@app.get('/api/store/products')
def store_products(query:str|None=None,category:str|None=None,brand:str|None=None,min_price:float|None=Query(default=None,ge=0),max_price:float|None=Query(default=None,ge=0),in_stock:bool|None=None,screen_size_inches:float|None=Query(default=None,ge=1,le=120),resolution:str|None=None,smart_tv:bool|None=None,limit:int=Query(default=24,ge=1,le=100)):
    return mock.search_products(query,category,brand,min_price,max_price,in_stock,screen_size_inches,resolution,smart_tv,limit)

@app.get('/api/store/products/{slug}')
def store_product(slug:str):
    p=mock.product_by_slug(slug)
    if not p: raise HTTPException(404,'Product not found')
    return {'product':p}

@app.post('/api/auth/login')
def login(payload:LoginRequest,request:Request):
    if not authenticate_admin(payload.email,payload.password,settings): raise HTTPException(status.HTTP_401_UNAUTHORIZED,'Invalid credentials')
    request.session[ADMIN_SESSION_KEY]={'user_id':settings.admin_user_id,'merchant_id':settings.merchant_id,'email':settings.admin_email,'name':'Alex Morgan'}; return {'success':True}

@app.post('/api/auth/logout')
def logout(request:Request): request.session.clear(); return {'success':True}

@app.get('/api/admin/me')
def admin_me(request:Request): return {**require_admin(request,settings),'merchant_name':'Mercury Store'}
@app.get('/api/admin/dashboard')
def dashboard(request:Request): require_admin(request,settings); return mock.dashboard()
@app.get('/api/admin/orders')
def orders(request:Request,status_filter:str|None=Query(default=None,alias='status'),limit:int=Query(default=100,ge=1,le=500)): require_admin(request,settings); rows=mock.recent_orders(limit,status_filter); return {'count':len(rows),'orders':rows}
@app.get('/api/admin/inventory')
def inventory(request:Request): require_admin(request,settings); rows=mock.inventory(); return {'count':len(rows),'inventory':rows}
@app.get('/api/admin/customers')
def customers(request:Request,limit:int=Query(default=100,ge=1,le=500)):
    require_admin(request,settings); rows=[]
    for c in mock.customers[:limit]:
        x=mock.customer(c['id']); rows.append({k:x[k] for k in ['id','name','email','segment','city','orders_count','lifetime_value']})
    rows.sort(key=lambda r:r['lifetime_value'],reverse=True); return {'count':len(rows),'customers':rows}
@app.get('/api/admin/shipments')
def shipments(request:Request,status_filter:str|None=Query(default=None,alias='status'),limit:int=Query(default=100,ge=1,le=500)): require_admin(request,settings); rows=mock.shipments_status(limit,status_filter); return {'count':len(rows),'shipments':rows}
@app.get('/api/admin/analytics')
def analytics(request:Request,days:int=Query(default=15,ge=1,le=120)): require_admin(request,settings); return mock.sales_analytics(days)
@app.get('/api/admin/forecast')
def forecast(request:Request,days:int=Query(default=30,ge=7,le=60)): require_admin(request,settings); return mock.forecast(days)
@app.get('/api/admin/reports')
def reports(request:Request): require_admin(request,settings); rows=db.list_reports(settings.merchant_id); return {'count':len(rows),'reports':rows}

async def ensure_binding(subject_key,surface_kind,public_id,access_key,metadata):
    existing=db.get_chat_binding(subject_key,surface_kind,public_id)
    if existing:return {'binding_id':existing['id'],'session_id':existing['woobe_session_id'],'target_release_id':existing['target_release_id'],'surface_id':public_id}
    try: remote=await woobe.create_session(public_id=public_id,access_key=access_key,external_reference=f'{surface_kind}:{subject_key}',metadata=metadata)
    except WoobeIntegrationError as exc: raise HTTPException(502,str(exc)) from exc
    bid=db.save_chat_binding(subject_key=subject_key,surface_kind=surface_kind,surface_public_id=public_id,woobe_session_id=remote.session_id,target_release_id=remote.target_release_id)
    return {'binding_id':bid,'session_id':remote.session_id,'target_release_id':remote.target_release_id,'surface_id':public_id}

@app.post('/api/chat/store/session')
async def store_session(payload:StoreChatRequest):
    if not settings.store_surface_configured: raise HTTPException(503,'Shopping Assistant ChatSurface is not configured')
    return await ensure_binding(payload.client_id,'store',settings.woobe_store_chat_surface_public_id,settings.woobe_store_chat_surface_access_key,{'application':'Mercury Store','surface_role':'shopping-assistant','client_id':payload.client_id})
@app.post('/api/chat/store/token')
async def store_token(payload:StoreChatRequest):
    if not settings.store_surface_configured: raise HTTPException(503,'Shopping Assistant ChatSurface is not configured')
    b=db.get_chat_binding(payload.client_id,'store',settings.woobe_store_chat_surface_public_id)
    if not b: raise HTTPException(404,'Shopping Assistant session not initialized')
    try:t=await woobe.issue_token(public_id=settings.woobe_store_chat_surface_public_id,access_key=settings.woobe_store_chat_surface_access_key,session_id=b['woobe_session_id'])
    except WoobeIntegrationError as exc: raise HTTPException(502,str(exc)) from exc
    return {'surface_id':settings.woobe_store_chat_surface_public_id,'session_id':b['woobe_session_id'],**t}
@app.post('/api/chat/admin/session')
async def admin_session(request:Request):
    p=require_admin(request,settings)
    if not settings.admin_surface_configured: raise HTTPException(503,'Merchant Assistant ChatSurface is not configured')
    return await ensure_binding(p['user_id'],'admin',settings.woobe_admin_chat_surface_public_id,settings.woobe_admin_chat_surface_access_key,{'application':'Mercury Merchant Console','surface_role':'merchant-operations-assistant','merchant_id':settings.merchant_id,'user_id':p['user_id']})
@app.post('/api/chat/admin/token')
async def admin_token(request:Request):
    p=require_admin(request,settings)
    if not settings.admin_surface_configured: raise HTTPException(503,'Merchant Assistant ChatSurface is not configured')
    b=db.get_chat_binding(p['user_id'],'admin',settings.woobe_admin_chat_surface_public_id)
    if not b: raise HTTPException(404,'Merchant Assistant session not initialized')
    try:t=await woobe.issue_token(public_id=settings.woobe_admin_chat_surface_public_id,access_key=settings.woobe_admin_chat_surface_access_key,session_id=b['woobe_session_id'])
    except WoobeIntegrationError as exc: raise HTTPException(502,str(exc)) from exc
    return {'surface_id':settings.woobe_admin_chat_surface_public_id,'session_id':b['woobe_session_id'],**t}

def store_guard(auth): require_bearer(settings.woobe_store_tool_api_key,auth)
def admin_guard(auth): require_bearer(settings.woobe_admin_tool_api_key,auth)

@app.get('/api/woobe-tools/store/search-products')
def tool_search(authorization:str|None=Header(default=None,alias='Authorization'),query:str|None=None,category:str|None=None,brand:str|None=None,min_price:float|None=Query(default=None,ge=0),max_price:float|None=Query(default=None,ge=0),in_stock:bool|None=True,screen_size_inches:float|None=Query(default=None,ge=1,le=120),resolution:str|None=None,smart_tv:bool|None=None,limit:int=Query(default=10,ge=1,le=30)):
    store_guard(authorization); return mock.search_products(query,category,brand,min_price,max_price,in_stock,screen_size_inches,resolution,smart_tv,limit)
@app.get('/api/woobe-tools/store/product')
def tool_product(authorization:str|None=Header(default=None,alias='Authorization'),slug:str=Query(...)):
    store_guard(authorization); p=mock.product_by_slug(slug)
    if not p:raise HTTPException(404,'Product not found')
    return {'product':p}
@app.get('/api/woobe-tools/store/categories')
def tool_categories(authorization:str|None=Header(default=None,alias='Authorization')): store_guard(authorization); return {'categories':mock.categories}

@app.get('/api/woobe-tools/admin/sales-analytics')
def tool_analytics(authorization:str|None=Header(default=None,alias='Authorization'),days:int=Query(default=15,ge=1,le=120)): admin_guard(authorization); return mock.sales_analytics(days)
@app.get('/api/woobe-tools/admin/forecast')
def tool_forecast(authorization:str|None=Header(default=None,alias='Authorization'),days:int=Query(default=30,ge=7,le=60)): admin_guard(authorization); return mock.forecast(days)
@app.get('/api/woobe-tools/admin/inventory')
def tool_inventory(authorization:str|None=Header(default=None,alias='Authorization')): admin_guard(authorization); rows=mock.inventory(); return {'count':len(rows),'inventory':rows}
@app.get('/api/woobe-tools/admin/orders')
def tool_orders(authorization:str|None=Header(default=None,alias='Authorization'),status_filter:str|None=Query(default=None,alias='status'),limit:int=Query(default=50,ge=1,le=200)): admin_guard(authorization); rows=mock.recent_orders(limit,status_filter); return {'count':len(rows),'orders':rows}
@app.get('/api/woobe-tools/admin/customer')
def tool_customer(authorization:str|None=Header(default=None,alias='Authorization'),customer_id:str=Query(...)):
    admin_guard(authorization); c=mock.customer(customer_id)
    if not c:raise HTTPException(404,'Customer not found')
    return {'customer':c}
@app.get('/api/woobe-tools/admin/shipments')
def tool_shipments(authorization:str|None=Header(default=None,alias='Authorization'),status_filter:str|None=Query(default=None,alias='status'),limit:int=Query(default=100,ge=1,le=200)): admin_guard(authorization); rows=mock.shipments_status(limit,status_filter); return {'count':len(rows),'shipments':rows}
@app.post('/api/woobe-tools/admin/reports',status_code=201)
def tool_report(payload:ReportCreateRequest,authorization:str|None=Header(default=None,alias='Authorization')): admin_guard(authorization); return {'report':db.create_report(merchant_id=settings.merchant_id,title=payload.title,period_label=payload.period_label,executive_summary=payload.executive_summary,findings=payload.findings,recommendations=payload.recommendations)}
