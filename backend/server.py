from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "user"  # user or admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    role: str = "user"

class ScrapItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    scrap_type: str  # Metal, Paper, Plastic, Glass, Electronics
    weight: float  # in kg
    price_offered: float  # price offered by user
    status: str = "pending"  # pending, approved, rejected, sold
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScrapItemCreate(BaseModel):
    scrap_type: str
    weight: float
    price_offered: float
    description: Optional[str] = None

class ScrapItemUpdate(BaseModel):
    status: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact: str
    address: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyCreate(BaseModel):
    name: str
    contact: str
    address: str
    email: Optional[str] = None

class Sale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scrap_item_id: str
    company_id: str
    selling_price: float
    profit: float
    sold_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SaleCreate(BaseModel):
    scrap_item_id: str
    company_id: str
    selling_price: float

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    scrap_item_id: str
    amount: float
    transaction_type: str  # buy, sell
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionData(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str

# Helper functions
async def verify_session_token(session_token: str) -> Optional[User]:
    """Verify session token and return user data"""
    try:
        # Check if session exists in database
        session = await db.sessions.find_one({"session_token": session_token})
        if not session:
            return None
        
        # Check if session is expired (7 days)
        if session.get('expires_at') and session['expires_at'] < datetime.now(timezone.utc):
            await db.sessions.delete_one({"session_token": session_token})
            return None
        
        # Get user data
        user = await db.users.find_one({"id": session["user_id"]})
        return User(**user) if user else None
    except Exception as e:
        logging.error(f"Error verifying session: {e}")
        return None

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session cookie or Authorization header"""
    session_token = None
    
    # Try to get from cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    return await verify_session_token(session_token)

async def require_auth(request: Request) -> User:
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(request: Request) -> User:
    """Require admin authentication"""
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Initialize admin user
async def create_admin_user():
    """Create default admin user if not exists"""
    admin_email = "admin@scrapmaster.com"
    existing_admin = await db.users.find_one({"email": admin_email})
    
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            name="System Admin",
            role="admin"
        )
        await db.users.insert_one(admin_user.dict())
        logging.info("Admin user created successfully")

# Auth routes
@api_router.get("/auth/login")
async def initiate_login():
    """Redirect to Emergent Auth"""
    preview_url = os.environ.get('FRONTEND_URL', 'https://scrapmaster-1.preview.emergentagent.com')
    auth_url = f"https://auth.emergentagent.com/?redirect={preview_url}"
    return {"auth_url": auth_url}

@api_router.get("/auth/profile")
async def get_profile(request: Request):
    """Get user profile from session"""
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        # Call Emergent Auth API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            session_data = SessionData(**response.json())
            
            # Check if user exists, create if not
            existing_user = await db.users.find_one({"email": session_data.email})
            
            if not existing_user:
                # Create new user
                user = User(
                    email=session_data.email,
                    name=session_data.name,
                    picture=session_data.picture,
                    role="user"
                )
                await db.users.insert_one(user.dict())
            else:
                user = User(**existing_user)
            
            # Create session
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            session_record = {
                "user_id": user.id,
                "session_token": session_data.session_token,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            }
            
            # Update or insert session
            await db.sessions.update_one(
                {"session_token": session_data.session_token},
                {"$set": session_record},
                upsert=True
            )
            
            return {
                "user": user,
                "session_token": session_data.session_token
            }
    
    except httpx.RequestError as e:
        logging.error(f"Auth API error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    user = await get_current_user(request)
    if user:
        session_token = request.cookies.get("session_token")
        if session_token:
            await db.sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

# User routes
@api_router.get("/users/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    user = await require_auth(request)
    return user

# Scrap item routes
@api_router.post("/scrap-items", response_model=ScrapItem)
async def create_scrap_item(item: ScrapItemCreate, request: Request):
    """Create new scrap item"""
    user = await require_auth(request)
    
    scrap_item = ScrapItem(
        user_id=user.id,
        **item.dict()
    )
    
    await db.scrap_items.insert_one(scrap_item.dict())
    
    # Create transaction record
    transaction = Transaction(
        user_id=user.id,
        scrap_item_id=scrap_item.id,
        amount=scrap_item.price_offered,
        transaction_type="buy"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return scrap_item

@api_router.get("/scrap-items", response_model=List[ScrapItem])
async def get_scrap_items(request: Request):
    """Get scrap items for current user"""
    user = await require_auth(request)
    
    scrap_items = await db.scrap_items.find({"user_id": user.id}).to_list(1000)
    return [ScrapItem(**item) for item in scrap_items]

@api_router.get("/scrap-items/all", response_model=List[dict])
async def get_all_scrap_items(request: Request):
    """Get all scrap items with user info (admin only)"""
    await require_admin(request)
    
    # Aggregation to join with users
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }
        },
        {
            "$unwind": "$user"
        },
        {
            "$project": {
                "id": 1,
                "scrap_type": 1,
                "weight": 1,
                "price_offered": 1,
                "status": 1,
                "description": 1,
                "created_at": 1,
                "updated_at": 1,
                "user_name": "$user.name",
                "user_email": "$user.email"
            }
        }
    ]
    
    scrap_items = await db.scrap_items.aggregate(pipeline).to_list(1000)
    return scrap_items

@api_router.put("/scrap-items/{item_id}/status")
async def update_scrap_item_status(item_id: str, update: ScrapItemUpdate, request: Request):
    """Update scrap item status (admin only)"""
    await require_admin(request)
    
    result = await db.scrap_items.update_one(
        {"id": item_id},
        {"$set": update.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scrap item not found")
    
    return {"message": "Status updated successfully"}

# Company routes
@api_router.post("/companies", response_model=Company)
async def create_company(company: CompanyCreate, request: Request):
    """Create new company (admin only)"""
    await require_admin(request)
    
    company_obj = Company(**company.dict())
    await db.companies.insert_one(company_obj.dict())
    return company_obj

@api_router.get("/companies", response_model=List[Company])
async def get_companies(request: Request):
    """Get all companies (admin only)"""
    await require_admin(request)
    
    companies = await db.companies.find().to_list(1000)
    return [Company(**company) for company in companies]

# Sales routes
@api_router.post("/sales", response_model=Sale)
async def create_sale(sale: SaleCreate, request: Request):
    """Sell scrap to company (admin only)"""
    await require_admin(request)
    
    # Get scrap item to calculate profit
    scrap_item = await db.scrap_items.find_one({"id": sale.scrap_item_id})
    if not scrap_item:
        raise HTTPException(status_code=404, detail="Scrap item not found")
    
    if scrap_item["status"] != "approved":
        raise HTTPException(status_code=400, detail="Can only sell approved scrap items")
    
    # Calculate profit
    profit = sale.selling_price - scrap_item["price_offered"]
    
    sale_obj = Sale(
        profit=profit,
        **sale.dict()
    )
    
    await db.sales.insert_one(sale_obj.dict())
    
    # Update scrap item status to sold
    await db.scrap_items.update_one(
        {"id": sale.scrap_item_id},
        {"$set": {"status": "sold", "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Create sell transaction
    transaction = Transaction(
        user_id=scrap_item["user_id"],
        scrap_item_id=sale.scrap_item_id,
        amount=sale.selling_price,
        transaction_type="sell"
    )
    await db.transactions.insert_one(transaction.dict())
    
    return sale_obj

@api_router.get("/sales", response_model=List[dict])
async def get_sales(request: Request):
    """Get all sales with details (admin only)"""
    await require_admin(request)
    
    pipeline = [
        {
            "$lookup": {
                "from": "scrap_items",
                "localField": "scrap_item_id",
                "foreignField": "id",
                "as": "scrap_item"
            }
        },
        {
            "$lookup": {
                "from": "companies",
                "localField": "company_id",
                "foreignField": "id",
                "as": "company"
            }
        },
        {
            "$unwind": "$scrap_item"
        },
        {
            "$unwind": "$company"
        }
    ]
    
    sales = await db.sales.aggregate(pipeline).to_list(1000)
    return sales

# Dashboard routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics"""
    user = await require_auth(request)
    
    if user.role == "admin":
        # Admin dashboard stats
        total_scrap_items = await db.scrap_items.count_documents({})
        pending_items = await db.scrap_items.count_documents({"status": "pending"})
        approved_items = await db.scrap_items.count_documents({"status": "approved"})
        sold_items = await db.scrap_items.count_documents({"status": "sold"})
        
        # Calculate total revenue and profit
        sales_pipeline = [
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$selling_price"},
                "total_profit": {"$sum": "$profit"}
            }}
        ]
        
        sales_stats = await db.sales.aggregate(sales_pipeline).to_list(1)
        total_revenue = sales_stats[0]["total_revenue"] if sales_stats else 0
        total_profit = sales_stats[0]["total_profit"] if sales_stats else 0
        
        return {
            "total_scrap_items": total_scrap_items,
            "pending_items": pending_items,
            "approved_items": approved_items,
            "sold_items": sold_items,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "total_companies": await db.companies.count_documents({})
        }
    else:
        # User dashboard stats
        user_scrap_items = await db.scrap_items.count_documents({"user_id": user.id})
        user_pending = await db.scrap_items.count_documents({"user_id": user.id, "status": "pending"})
        user_approved = await db.scrap_items.count_documents({"user_id": user.id, "status": "approved"})
        user_sold = await db.scrap_items.count_documents({"user_id": user.id, "status": "sold"})
        
        # Calculate user earnings
        user_transactions = await db.transactions.find({"user_id": user.id, "transaction_type": "sell"}).to_list(1000)
        total_earnings = sum(t["amount"] for t in user_transactions)
        
        return {
            "total_items": user_scrap_items,
            "pending_items": user_pending,
            "approved_items": user_approved,
            "sold_items": user_sold,
            "total_earnings": total_earnings
        }

# Scrap types endpoint
@api_router.get("/scrap-types")
async def get_scrap_types():
    """Get available scrap types"""
    return {
        "scrap_types": [
            "Metal",
            "Paper", 
            "Plastic",
            "Glass",
            "Electronics"
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db():
    await create_admin_user()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()