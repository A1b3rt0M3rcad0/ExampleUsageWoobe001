import type { AdminMe, Customer, Dashboard, InventoryRow, Order, ProductSearch, Report, Shipment } from './types'
const API_BASE=import.meta.env.VITE_APP_API_BASE_URL??'http://localhost:8001'
async function request<T>(path:string,init?:RequestInit):Promise<T>{const response=await fetch(`${API_BASE}${path}`,{...init,credentials:'include',headers:{'Content-Type':'application/json',...(init?.headers??{})}});if(!response.ok){let detail=`HTTP ${response.status}`;try{const p=await response.json();detail=p.detail??detail}catch{}throw new Error(detail)}return response.json() as Promise<T>}
function qs(values:Record<string,string|number|boolean|undefined>){const p=new URLSearchParams();Object.entries(values).forEach(([k,v])=>{if(v!==undefined&&v!=='')p.set(k,String(v))});return p.toString()?`?${p}`:''}
export const api={
 storeProducts:(v:{query?:string;category?:string;max_price?:number;in_stock?:boolean;screen_size_inches?:number}={})=>request<ProductSearch>(`/api/store/products${qs(v)}`),
 categories:()=>request<{categories:string[]}>('/api/store/categories'),
 login:(email:string,password:string)=>request<{success:boolean}>('/api/auth/login',{method:'POST',body:JSON.stringify({email,password})}),
 logout:()=>request<{success:boolean}>('/api/auth/logout',{method:'POST'}),
 adminMe:()=>request<AdminMe>('/api/admin/me'), dashboard:()=>request<Dashboard>('/api/admin/dashboard'),
 orders:()=>request<{count:number;orders:Order[]}>('/api/admin/orders?limit=120'), inventory:()=>request<{count:number;inventory:InventoryRow[]}>('/api/admin/inventory'),
 customers:()=>request<{count:number;customers:Customer[]}>('/api/admin/customers'), shipments:()=>request<{count:number;shipments:Shipment[]}>('/api/admin/shipments'), reports:()=>request<{count:number;reports:Report[]}>('/api/admin/reports'),
 initializeStoreChat:(client_id:string)=>request<{surface_id:string;session_id:string}>('/api/chat/store/session',{method:'POST',body:JSON.stringify({client_id})}),
 storeChatToken:(client_id:string)=>request<{surface_id:string;session_id:string;session_token:string;expires_in:number}>('/api/chat/store/token',{method:'POST',body:JSON.stringify({client_id})}),
 initializeAdminChat:()=>request<{surface_id:string;session_id:string}>('/api/chat/admin/session',{method:'POST'}),
 adminChatToken:()=>request<{surface_id:string;session_id:string;session_token:string;expires_in:number}>('/api/chat/admin/token',{method:'POST'})
}
