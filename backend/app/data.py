from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import math, random, re, unicodedata
from typing import Any


def slugify(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value).encode('ascii','ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+','-',normalized.lower()).strip('-')


def P(name, brand, category, price, stock, aisle, shelf, tags, attributes, popularity, trend):
    slug = slugify(name)
    return {'id':f"prd_{slug.replace('-','_')}",'slug':slug,'name':name,'brand':brand,'category':category,'price':float(price),'stock':stock,'available':stock>0,'aisle':aisle,'shelf':shelf,'description':f'{name} — item do catálogo demonstrativo da Mercury Store.','tags':tags,'attributes':attributes,'_popularity':popularity,'_trend':trend}

PRODUCTS = [
P('Samsung Smart TV LED 27"','Samsung','Televisions',1299,8,'A1','TV-02',['tv','smart tv','led','compacta'],{'screen_size_inches':27,'resolution':'Full HD','screen_type':'LED','smart_tv':True},1.05,.12),
P('LG Smart TV 27" Full HD','LG','Televisions',1399,0,'A1','TV-03',['tv','smart tv','full hd'],{'screen_size_inches':27,'resolution':'Full HD','screen_type':'LED','smart_tv':True},.55,-.18),
P('Samsung Crystal UHD 43"','Samsung','Televisions',2199,14,'A1','TV-05',['tv','4k','smart tv'],{'screen_size_inches':43,'resolution':'4K','screen_type':'LED','smart_tv':True},1.35,.28),
P('LG UHD AI ThinQ 50"','LG','Televisions',2699,9,'A1','TV-07',['tv','4k','smart tv','alexa'],{'screen_size_inches':50,'resolution':'4K','screen_type':'LED','smart_tv':True},1.25,.31),
P('TCL QLED 55" C655','TCL','Televisions',2999,5,'A1','TV-09',['tv','qled','4k','gaming'],{'screen_size_inches':55,'resolution':'4K','screen_type':'QLED','smart_tv':True},1.15,.52),
P('Philips Roku TV 32"','Philips','Televisions',1199,18,'A1','TV-01',['tv','roku','compacta'],{'screen_size_inches':32,'resolution':'HD','screen_type':'LED','smart_tv':True},.92,-.08),
P('Samsung Odyssey G5 27"','Samsung','Monitors',1799,12,'A2','MON-06',['monitor','gaming','144hz','27 polegadas'],{'screen_size_inches':27,'resolution':'QHD','refresh_rate_hz':144,'panel':'VA'},1.2,.44),
P('LG UltraGear 27GN65R 27"','LG','Monitors',1499,7,'A2','MON-04',['monitor','gaming','144hz'],{'screen_size_inches':27,'resolution':'Full HD','refresh_rate_hz':144,'panel':'IPS'},1.08,.23),
P('Dell P2425H 24"','Dell','Monitors',1299,21,'A2','MON-02',['monitor','office','ips'],{'screen_size_inches':24,'resolution':'Full HD','refresh_rate_hz':100,'panel':'IPS'},.88,.04),
P('AOC Hero 24" 165Hz','AOC','Monitors',1099,16,'A2','MON-01',['monitor','gaming','165hz'],{'screen_size_inches':24,'resolution':'Full HD','refresh_rate_hz':165,'panel':'IPS'},1,.18),
P('Sony WH-1000XM6','Sony','Audio',2799,12,'B1','AUD-08',['headphone','bluetooth','noise cancelling','anc'],{'connectivity':'Bluetooth','noise_cancelling':True,'battery_hours':30,'type':'over-ear'},1.6,.48),
P('Edifier W820NB Plus','Edifier','Audio',449,24,'B1','AUD-03',['headphone','bluetooth','noise cancelling','custo-benefício'],{'connectivity':'Bluetooth','noise_cancelling':True,'battery_hours':49,'type':'over-ear'},1.45,.62),
P('JBL Quantum 360 Wireless','JBL','Audio',399,19,'B1','AUD-02',['headset','wireless','gaming'],{'connectivity':'Wireless','noise_cancelling':False,'battery_hours':22,'type':'headset'},1.3,.33),
P('HyperX Cloud III Wireless','HyperX','Audio',489,4,'B1','AUD-04',['headset','wireless','gaming'],{'connectivity':'Wireless','noise_cancelling':False,'battery_hours':120,'type':'headset'},1.5,.71),
P('Galaxy Buds3 Pro','Samsung','Audio',1299,17,'B1','AUD-06',['earbuds','bluetooth','anc'],{'connectivity':'Bluetooth','noise_cancelling':True,'battery_hours':26,'type':'in-ear'},1.28,.25),
P('JBL Tune 520BT','JBL','Audio',219,31,'B1','AUD-01',['headphone','bluetooth','barato'],{'connectivity':'Bluetooth','noise_cancelling':False,'battery_hours':57,'type':'on-ear'},1.32,.09),
P('Logitech MX Mechanical Mini','Logitech','Keyboards',799,11,'B2','KEY-07',['teclado','mecânico','bluetooth','silencioso'],{'layout':'US','switch':'Tactile Quiet','wireless':True,'backlight':True},1.4,.68),
P('Keychron K8 Pro ABNT2','Keychron','Keyboards',699,13,'B2','KEY-06',['teclado','mecânico','abnt2','bluetooth'],{'layout':'ABNT2','switch':'Brown','wireless':True,'backlight':True},1.35,.55),
P('Redragon Kumara Pro','Redragon','Keyboards',319,22,'B2','KEY-02',['teclado','mecânico','abnt2','gaming'],{'layout':'ABNT2','switch':'Brown','wireless':True,'backlight':True},1.25,.14),
P('Microsoft Wired Keyboard 600','Microsoft','Keyboards',129,46,'B2','KEY-01',['teclado','membrana','office'],{'layout':'ABNT2','switch':'Membrane','wireless':False,'backlight':False},.62,-.52),
P('Logitech G305 Lightspeed','Logitech','Mice',249,26,'B3','MOU-04',['mouse','fps','wireless','gaming'],{'dpi':12000,'wireless':True,'weight_g':99},1.46,.37),
P('Razer DeathAdder V3','Razer','Mice',329,10,'B3','MOU-07',['mouse','fps','gaming','leve'],{'dpi':30000,'wireless':False,'weight_g':59},1.28,.41),
P('Logitech MX Master 3S','Logitech','Mice',649,15,'B3','MOU-08',['mouse','produtividade','bluetooth'],{'dpi':8000,'wireless':True,'weight_g':141},1.18,.15),
P('Mouse Basic USB 1000 DPI','Mercury Basics','Mice',49,78,'B3','MOU-01',['mouse','office','usb','barato'],{'dpi':1000,'wireless':False,'weight_g':86},.48,-.58),
P('MacBook Air M4 13 16GB 256GB','Apple','Notebooks',7999,6,'C1','NB-09',['notebook','macbook','m4','leve'],{'memory_gb':16,'storage_gb':256,'processor':'Apple M4','screen_size_inches':13.6},.78,.22),
P('Dell Inspiron 14 Ryzen 7 16GB','Dell','Notebooks',4399,9,'C1','NB-05',['notebook','ryzen','trabalho'],{'memory_gb':16,'storage_gb':512,'processor':'Ryzen 7','screen_size_inches':14},.95,.36),
P('Lenovo LOQ RTX 4060 16GB','Lenovo','Notebooks',6499,3,'C1','NB-08',['notebook','gaming','rtx 4060'],{'memory_gb':16,'storage_gb':512,'processor':'Core i7','gpu':'RTX 4060','screen_size_inches':15.6},.9,.49),
P('Acer Aspire 5 i5 8GB','Acer','Notebooks',2999,20,'C1','NB-03',['notebook','office','i5'],{'memory_gb':8,'storage_gb':512,'processor':'Core i5','screen_size_inches':15.6},1,-.04),
P('SanDisk Extreme Portable SSD 1TB','SanDisk','Storage',699,14,'C2','STO-06',['ssd','externo','usb-c','1tb'],{'storage_gb':1000,'interface':'USB-C','type':'SSD'},1.06,.32),
P('Kingston NV3 NVMe 1TB','Kingston','Storage',499,25,'C2','STO-04',['ssd','nvme','1tb'],{'storage_gb':1000,'interface':'PCIe 4.0','type':'NVMe'},1.3,.46),
P('Seagate Expansion 2TB','Seagate','Storage',549,18,'C2','STO-03',['hd','externo','2tb'],{'storage_gb':2000,'interface':'USB 3.0','type':'HDD'},.72,-.29),
P('Anker USB-C Hub 8-in-1','Anker','Accessories',389,7,'C3','ACC-08',['hub','usb-c','hdmi','notebook'],{'ports':8,'hdmi':True,'power_delivery_w':100},1.42,.73),
P('Baseus USB-C Hub 6-in-1','Baseus','Accessories',249,16,'C3','ACC-05',['hub','usb-c','hdmi'],{'ports':6,'hdmi':True,'power_delivery_w':100},1.18,.39),
P('Logitech C920s Pro HD','Logitech','Accessories',429,27,'C3','ACC-04',['webcam','full hd','streaming'],{'resolution':'Full HD','microphone':True,'fps':30},.67,-.47),
P('Webcam Basic HD 720p','Mercury Basics','Accessories',119,62,'C3','ACC-01',['webcam','720p','barata'],{'resolution':'HD','microphone':True,'fps':30},.42,-.72),
P('PlayStation 5 Slim','Sony','Gaming',3499,5,'D1','GAM-09',['console','playstation','ps5'],{'storage_gb':1000,'edition':'Disc'},1.15,.21),
P('Xbox Series S 512GB','Microsoft','Gaming',2499,10,'D1','GAM-06',['console','xbox','game pass'],{'storage_gb':512,'edition':'Digital'},.92,-.12),
P('Nintendo Switch OLED','Nintendo','Gaming',2299,13,'D1','GAM-05',['console','switch','portátil'],{'storage_gb':64,'screen_size_inches':7,'edition':'OLED'},1.02,.05),
P('DualSense Wireless Controller','Sony','Gaming',449,23,'D1','GAM-03',['controle','ps5','wireless'],{'connectivity':'Bluetooth','platform':'PS5'},1.2,.12),
P('Xbox Wireless Controller','Microsoft','Gaming',399,21,'D1','GAM-02',['controle','xbox','wireless'],{'connectivity':'Bluetooth','platform':'Xbox/PC'},1.08,.08),
P('Elgato Stream Deck MK.2','Elgato','Creator',899,8,'D2','CRT-06',['stream deck','creator','atalhos'],{'keys':15,'connectivity':'USB-C'},.78,.48),
P('Fifine K688 USB/XLR','Fifine','Creator',499,17,'D2','CRT-04',['microfone','usb','xlr','podcast'],{'connectivity':'USB/XLR','pattern':'Cardioid'},1.02,.34),
P('Blue Yeti Nano','Logitech','Creator',699,11,'D2','CRT-05',['microfone','usb','podcast'],{'connectivity':'USB','pattern':'Cardioid/Omni'},.82,-.16),
]

FIRST=['Ana','Bruno','Carla','Diego','Elisa','Felipe','Gabriela','Henrique','Isabela','João','Karina','Lucas','Marina','Nicolas','Olivia','Paulo','Renata','Samuel','Talita','Victor']
LAST=['Almeida','Barbosa','Costa','Dias','Ferreira','Gomes','Lima','Martins','Mendes','Oliveira','Pereira','Ramos','Rocha','Santos','Silva','Souza']

class MockCommerceData:
    def __init__(self, public_store_base_url: str):
        self.public_store_base_url=public_store_base_url.rstrip('/'); self.now=datetime.now(timezone.utc)
        self._internal={p['id']:p for p in PRODUCTS}; self.products=[self._public(p) for p in PRODUCTS]
        self.customers=self._customers(); self.orders=self._orders(120); self.shipments=self._shipments()
        self._customer_map={c['id']:c for c in self.customers}

    def _public(self,p):
        return {k:v for k,v in p.items() if not k.startswith('_')}|{'product_url':f"{self.public_store_base_url}/?product={p['slug']}"}

    def _customers(self):
        rng=random.Random(20260811); rows=[]
        for i in range(72):
            f,l=rng.choice(FIRST),rng.choice(LAST)
            rows.append({'id':f'cus_{i+1:04d}','name':f'{f} {l}','email':f'{f.lower()}.{l.lower()}{i+1}@example.test','segment':rng.choices(['standard','repeat','vip'],[62,28,10])[0],'city':rng.choice(['São Paulo','Florianópolis','Curitiba','Porto Alegre','Belo Horizonte','Campinas'])})
        rows[0].update({'name':'Marina Costa','email':'marina.costa@example.test','segment':'vip','city':'Florianópolis'})
        return rows

    def _orders(self,days):
        rows=[]
        for day_index in range(days):
            date=(self.now-timedelta(days=days-1-day_index)).replace(hour=12,minute=0,second=0,microsecond=0); rng=random.Random(8800+day_index); pos=day_index/max(days-1,1)
            count=rng.randint(14,26)+(4 if day_index>=days-15 else 0)
            ids=[]; weights=[]
            for p in PRODUCTS:
                ids.append(p['id']); weights.append(max(.05,p['_popularity']*(1+p['_trend']*(pos-.5))*(1+.10*math.sin((day_index/7)*math.tau))))
            for _ in range(count):
                customer=rng.choice(self.customers); selected=rng.choices(ids,weights=weights,k=rng.choices([1,2,3],[70,24,6])[0]); items=[]; total=0
                for pid,q in Counter(selected).items():
                    p=self._internal[pid]; q=min(q,2); line=round(p['price']*q,2); total+=line; items.append({'product_id':pid,'product_name':p['name'],'category':p['category'],'quantity':q,'unit_price':p['price'],'line_total':line})
                created=date+timedelta(hours=rng.randint(0,10),minutes=rng.randint(0,59))
                rows.append({'id':f'ORD-{10000+len(rows)}','customer_id':customer['id'],'customer_name':customer['name'],'customer_segment':customer['segment'],'created_at':created.isoformat(),'status':rng.choices(['delivered','shipped','processing','cancelled'],[62,18,17,3])[0],'total':round(total,2),'items':items})
        rows[-35].update({'customer_id':self.customers[0]['id'],'customer_name':self.customers[0]['name'],'customer_segment':'vip','status':'shipped'})
        return rows

    def _shipments(self):
        rng=random.Random(9911); candidates=[o for o in self.orders[-240:] if o['status'] in {'shipped','delivered'}]; rows=[]
        for i,o in enumerate(candidates[-120:]):
            delayed=i%17==0 or o['customer_id']==self.customers[0]['id']; status='delayed' if delayed else ('delivered' if o['status']=='delivered' else 'in_transit')
            rows.append({'id':f'SHP-{7000+i}','order_id':o['id'],'customer_id':o['customer_id'],'customer_name':o['customer_name'],'carrier':rng.choice(['Jadlog','Loggi','Correios','Total Express']),'status':status,'expected_at':(self.now+timedelta(days=4 if delayed else 2)).isoformat(),'last_event':'Carrier reported operational delay at regional hub' if delayed else 'Package moving through carrier network'})
        return rows

    @property
    def categories(self): return sorted({p['category'] for p in self.products})
    def product_by_slug(self,slug): return next((p for p in self.products if p['slug']==slug),None)

    def search_products(self,query=None,category=None,brand=None,min_price=None,max_price=None,in_stock=None,screen_size_inches=None,resolution=None,smart_tv=None,limit=20):
        q=(query or '').strip().lower(); cat=(category or '').strip().lower()
        if q in {'tv','televisao','televisão','television','televisions'} and not cat: cat='televisions'
        def ok(p):
            hay=' '.join([p['name'],p['brand'],p['category'],p['description'],*p['tags'],*[str(v) for v in p['attributes'].values()]]).lower()
            if q and not all(t in hay for t in q.split()): return False
            if cat and cat not in p['category'].lower(): return False
            if brand and brand.lower() not in p['brand'].lower(): return False
            if min_price is not None and p['price']<min_price: return False
            if max_price is not None and p['price']>max_price: return False
            if in_stock is not None and p['available'] is not in_stock: return False
            if screen_size_inches is not None and abs(float(p['attributes'].get('screen_size_inches',-999))-float(screen_size_inches))>.01: return False
            if resolution and resolution.lower() not in str(p['attributes'].get('resolution','')).lower(): return False
            if smart_tv is not None and p['attributes'].get('smart_tv') is not smart_tv: return False
            return True
        results=sorted([p for p in self.products if ok(p)],key=lambda p:(not p['available'],p['price']))
        alternatives=[]
        if not results and screen_size_inches is not None:
            candidates=[p for p in self.products if 'screen_size_inches' in p['attributes'] and (not cat or cat in p['category'].lower()) and (not brand or brand.lower() in p['brand'].lower()) and (in_stock is not True or p['available'])]
            alternatives=sorted(candidates,key=lambda p:abs(float(p['attributes']['screen_size_inches'])-float(screen_size_inches)))[:3]
        return {'query':{'text':query,'category':category,'brand':brand,'min_price':min_price,'max_price':max_price,'in_stock':in_stock,'screen_size_inches':screen_size_inches,'resolution':resolution,'smart_tv':smart_tv},'count':min(len(results),limit),'results':results[:limit],'alternatives':alternatives}

    def recent_orders(self,limit=100,status=None):
        rows=self.orders[-limit*3:]; rows=[o for o in rows if not status or o['status']==status]; return list(reversed(rows[-limit:]))

    def customer(self,cid):
        c=self._customer_map.get(cid)
        if not c:return None
        orders=[o for o in self.orders if o['customer_id']==cid]; spend=round(sum(o['total'] for o in orders if o['status']!='cancelled'),2)
        return {**c,'orders_count':len(orders),'lifetime_value':spend,'recent_orders':list(reversed(orders[-5:]))}

    def _aggregate(self,rows):
        pu=Counter(); pr=defaultdict(float); cu=Counter(); cr=defaultdict(float)
        for o in rows:
            for i in o['items']:
                pu[i['product_id']]+=i['quantity']; pr[i['product_id']]+=i['line_total']; cu[i['category']]+=i['quantity']; cr[i['category']]+=i['line_total']
        return pu,pr,cu,cr

    def sales_analytics(self,days=15):
        days=max(1,min(days,120)); current_start=self.now-timedelta(days=days); prev_start=current_start-timedelta(days=days)
        current=[o for o in self.orders if datetime.fromisoformat(o['created_at'])>=current_start and o['status']!='cancelled']; previous=[o for o in self.orders if prev_start<=datetime.fromisoformat(o['created_at'])<current_start and o['status']!='cancelled']
        pu,pr,cu,cr=self._aggregate(current); ppu,_,_,_=self._aggregate(previous); rows=[]
        for p in self.products:
            u,prev=pu[p['id']],ppu[p['id']]; growth=(100 if u>0 else 0) if prev==0 else round((u-prev)/prev*100,1)
            rows.append({'product_id':p['id'],'name':p['name'],'category':p['category'],'units':u,'revenue':round(pr[p['id']],2),'previous_units':prev,'growth_percent':growth,'stock':p['stock'],'product_url':p['product_url']})
        cats=sorted([{'category':c,'units':u,'revenue':round(cr[c],2)} for c,u in cu.items()],key=lambda x:x['revenue'],reverse=True)
        top=sorted(rows,key=lambda x:(x['revenue'],x['units']),reverse=True)[:8]; low=sorted([r for r in rows if r['units']<=8 or r['growth_percent']<-25],key=lambda x:(x['growth_percent'],x['units']))[:8]
        revenue=round(sum(o['total'] for o in current),2)
        return {'period_days':days,'revenue':revenue,'orders':len(current),'units_sold':sum(pu.values()),'average_order_value':round(revenue/max(len(current),1),2),'top_products':top,'top_categories':cats[:6],'low_performers':low}

    def _units(self,pid,start,end):
        total=0
        for o in self.orders:
            dt=datetime.fromisoformat(o['created_at'])
            if o['status']=='cancelled' or not(start<=dt<end): continue
            total+=sum(i['quantity'] for i in o['items'] if i['product_id']==pid)
        return total

    def forecast(self,days=30):
        days=max(7,min(days,60)); rows=[]
        for p in self.products:
            recent=self._units(p['id'],self.now-timedelta(days=30),self.now+timedelta(seconds=1)); previous=self._units(p['id'],self.now-timedelta(days=60),self.now-timedelta(days=30)); w1=self._units(p['id'],self.now-timedelta(days=7),self.now+timedelta(seconds=1)); w0=self._units(p['id'],self.now-timedelta(days=14),self.now-timedelta(days=7))
            g30=(recent-previous)/max(previous,1); g7=(w1-w0)/max(w0,1); g=max(-.65,min(.85,g30*.55+g7*.45)); expected=max(0,round(recent*(days/30)*(1+g*.35))); confidence=min(.93,max(.48,.5+min(recent,80)/200-abs(g7-g30)*.08)); risk='stockout' if expected>p['stock']*1.15 else ('tight' if expected>p['stock']*.75 else 'healthy')
            rows.append({'product_id':p['id'],'name':p['name'],'category':p['category'],'current_stock':p['stock'],'recent_30d_units':recent,'previous_30d_units':previous,'trend_percent':round(g*100,1),'expected_units':expected,'confidence':round(confidence,2),'stock_risk':risk,'product_url':p['product_url']})
        return {'forecast_days':days,'method':'deterministic mock demand model using 30-day, previous-30-day and recent-week sales velocity','products':rows,'rising_products':sorted([r for r in rows if r['trend_percent']>=18 and r['expected_units']>=5],key=lambda r:r['trend_percent'],reverse=True)[:8],'declining_products':sorted([r for r in rows if r['trend_percent']<=-18],key=lambda r:r['trend_percent'])[:8],'stock_risks':sorted([r for r in rows if r['stock_risk']=='stockout'],key=lambda r:r['expected_units']-r['current_stock'],reverse=True)[:8],'slow_movers':sorted([r for r in rows if r['expected_units']<=5],key=lambda r:(r['expected_units'],r['trend_percent']))[:8]}

    def inventory(self):
        fm={r['product_id']:r for r in self.forecast(30)['products']}; rows=[]
        for p in self.products:
            f=fm[p['id']]; rows.append({'product_id':p['id'],'name':p['name'],'category':p['category'],'stock':p['stock'],'price':p['price'],'expected_30d_demand':f['expected_units'],'stock_risk':f['stock_risk'],'product_url':p['product_url']})
        return sorted(rows,key=lambda r:(r['stock_risk']!='stockout',r['stock']-r['expected_30d_demand']))

    def shipments_status(self,limit=100,status=None):
        rows=[s for s in self.shipments if not status or s['status']==status]; return list(reversed(rows[-limit:]))

    def dashboard(self):
        a=self.sales_analytics(15); f=self.forecast(30)
        return {'merchant':{'name':'Mercury Store','environment':'Mock Commerce Demo'},'metrics':{'revenue_15d':a['revenue'],'orders_15d':a['orders'],'average_order_value_15d':a['average_order_value'],'products_at_stockout_risk':len(f['stock_risks']),'delayed_shipments':len([s for s in self.shipments if s['status']=='delayed'])},'top_products':a['top_products'][:5],'top_categories':a['top_categories'][:5],'rising_products':f['rising_products'][:5],'recent_orders':self.recent_orders(8)}
