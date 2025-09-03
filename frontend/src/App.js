import React, { useState, useEffect, createContext, useContext } from 'react';
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  // Mock admin user for demonstration - bypassing authentication
  const [user, setUser] = useState({
    id: "admin-demo-id",
    email: "admin@scrapmaster.com",
    name: "Admin Demo User",
    picture: "https://via.placeholder.com/40",
    role: "admin"
  });
  const [loading, setLoading] = useState(false); // Set to false since we're using mock data

  const login = (userData, sessionToken) => {
    setUser(userData);
    // Set cookie
    document.cookie = `session_token=${sessionToken}; path=/; max-age=${7 * 24 * 60 * 60}; secure; samesite=none`;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error('Logout error:', error);
    }
    setUser(null);
    document.cookie = 'session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  };

  const checkAuth = async () => {
    // Bypassed - using mock user
    setLoading(false);
  };

  useEffect(() => {
    // Auto-set mock admin user for demonstration
    setLoading(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// Profile page component to handle auth redirect
const ProfilePage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuthRedirect = async () => {
      const hash = location.hash;
      if (hash && hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1];
        
        try {
          const response = await axios.get(`${API}/auth/profile`, {
            headers: { 'X-Session-ID': sessionId }
          });
          
          login(response.data.user, response.data.session_token);
          navigate('/dashboard');
        } catch (error) {
          console.error('Auth error:', error);
          navigate('/');
        }
      } else {
        navigate('/');
      }
    };

    handleAuthRedirect();
  }, [location, login, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
};

// Login component
const Login = () => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/auth/login`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-2xl max-w-md w-full mx-4">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ScrapMaster</h1>
          <p className="text-gray-600">Efficient Scrap Management System</p>
        </div>
        
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Connecting...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              Login / Sign Up
            </>
          )}
        </button>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Secure authentication powered by Emergent</p>
        </div>
      </div>
    </div>
  );
};

// Add Scrap Item Component
const AddScrapForm = ({ onClose, onAdd }) => {
  const [formData, setFormData] = useState({
    scrap_type: 'Metal',
    weight: '',
    price_offered: '',
    description: ''
  });

  const scrapTypes = ['Metal', 'Paper', 'Plastic', 'Glass', 'Electronics'];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.weight && formData.price_offered) {
      const newItem = {
        id: `item-${Date.now()}`,
        ...formData,
        weight: parseFloat(formData.weight),
        price_offered: parseFloat(formData.price_offered),
        status: 'pending',
        created_at: new Date().toISOString()
      };
      onAdd(newItem);
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Add New Scrap Item</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Scrap Type</label>
            <select 
              value={formData.scrap_type}
              onChange={(e) => setFormData({...formData, scrap_type: e.target.value})}
              className="form-input"
            >
              {scrapTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
            <input
              type="number"
              step="0.1"
              value={formData.weight}
              onChange={(e) => setFormData({...formData, weight: e.target.value})}
              className="form-input"
              placeholder="Enter weight in kg"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Price Offered (₹)</label>
            <input
              type="number"
              step="0.01"
              value={formData.price_offered}
              onChange={(e) => setFormData({...formData, price_offered: e.target.value})}
              className="form-input"
              placeholder="Enter price in rupees"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="form-input"
              rows="3"
              placeholder="Brief description of the scrap item"
            />
          </div>
          
          <div className="flex space-x-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              Add Scrap Item
            </button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Scrap Items List Component
const ScrapItemsList = ({ items, onStatusChange, isAdmin }) => {
  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4-8-4m16 0v10l-8 4-8-4V7" />
        </svg>
        <p>No scrap items found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map(item => (
        <div key={item.id} className="card card-hover p-4">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h4 className="font-medium text-gray-900">{item.scrap_type}</h4>
                <span className={`px-2 py-1 text-xs rounded-full status-${item.status}`}>
                  {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                </span>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p><span className="font-medium">Weight:</span> {item.weight} kg</p>
                <p><span className="font-medium">Price:</span> ₹{item.price_offered}</p>
                {item.description && (
                  <p><span className="font-medium">Description:</span> {item.description}</p>
                )}
                <p><span className="font-medium">Date:</span> {new Date(item.created_at).toLocaleDateString()}</p>
              </div>
            </div>
            
            {isAdmin && item.status === 'pending' && (
              <div className="flex space-x-2 ml-4">
                <button
                  onClick={() => onStatusChange(item.id, 'approved')}
                  className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Approve
                </button>
                <button
                  onClick={() => onStatusChange(item.id, 'rejected')}
                  className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
const Dashboard = () => {
  const { user, logout } = useAuth();
  // Mock stats for demonstration
  const [stats, setStats] = useState({
    total_scrap_items: 156,
    pending_items: 23,
    approved_items: 89,
    sold_items: 44,
    total_revenue: 125000,
    total_profit: 45000,
    total_companies: 12
  });
  const [loading, setLoading] = useState(false); // Disabled for demo
  const [showAddForm, setShowAddForm] = useState(false);
  const [showScrapItems, setShowScrapItems] = useState(false);
  const [scrapItems, setScrapItems] = useState([
    {
      id: 'item-1',
      scrap_type: 'Metal',
      weight: 15.5,
      price_offered: 2500,
      status: 'pending',
      description: 'Old iron sheets and scraps',
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: 'item-2',
      scrap_type: 'Electronics',
      weight: 3.2,
      price_offered: 800,
      status: 'approved',
      description: 'Old computer parts',
      created_at: '2024-01-14T14:20:00Z'
    },
    {
      id: 'item-3',
      scrap_type: 'Paper',
      weight: 25.0,
      price_offered: 500,
      status: 'sold',
      description: 'Newspapers and magazines',
      created_at: '2024-01-13T09:15:00Z'
    }
  ]);

  useEffect(() => {
    // Mock data loaded, no API call needed for demo
  }, []);

  const fetchStats = async () => {
    // Disabled for demo - using mock data
    setLoading(false);
  };

  const handleAddScrapItem = (newItem) => {
    setScrapItems([newItem, ...scrapItems]);
    setStats(prev => ({
      ...prev,
      total_scrap_items: prev.total_scrap_items + 1,
      pending_items: prev.pending_items + 1
    }));
  };

  const handleStatusChange = (itemId, newStatus) => {
    setScrapItems(prev => prev.map(item => 
      item.id === itemId ? { ...item, status: newStatus } : item
    ));
    
    // Update stats based on status change
    setStats(prev => {
      const updates = { ...prev };
      if (newStatus === 'approved') {
        updates.pending_items -= 1;
        updates.approved_items += 1;
      } else if (newStatus === 'rejected') {
        updates.pending_items -= 1;
      }
      return updates;
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">ScrapMaster</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <img
                  src={user?.picture || 'https://via.placeholder.com/32'}
                  alt="Profile"
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm font-medium text-gray-700">{user?.name}</span>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  user?.role === 'admin' 
                    ? 'bg-purple-100 text-purple-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {user?.role}
                </span>
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {user?.role === 'admin' ? 'Admin Dashboard' : 'My Dashboard'}
          </h2>
          <p className="text-gray-600">
            {user?.role === 'admin' 
              ? 'Manage scrap items, companies, and sales'
              : 'Track your scrap submissions and earnings'
            }
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {user?.role === 'admin' ? (
            <>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4-8-4m16 0v10l-8 4-8-4V7" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Scrap Items</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.total_scrap_items || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Pending Items</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.pending_items || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                    <p className="text-2xl font-semibold text-gray-900">₹{stats.total_revenue || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Profit</p>
                    <p className="text-2xl font-semibold text-gray-900">₹{stats.total_profit || 0}</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4-8-4m16 0v10l-8 4-8-4V7" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">My Items</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.total_items || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Pending</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.pending_items || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Sold Items</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.sold_items || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Earnings</p>
                    <p className="text-2xl font-semibold text-gray-900">₹{stats.total_earnings || 0}</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {user?.role === 'admin' ? (
              <>
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">Manage Scrap Items</p>
                  </div>
                </button>
                
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">Manage Companies</p>
                  </div>
                </button>
                
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">View Reports</p>
                  </div>
                </button>
              </>
            ) : (
              <>
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">Add New Scrap</p>
                  </div>
                </button>
                
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">My Scrap History</p>
                  </div>
                </button>
                
                <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-5 5v-5zM4 19h8a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <p className="text-sm font-medium text-gray-600">Notifications</p>
                  </div>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Protected Route Component - Bypassed for demo
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  // Always allow access for demo purposes
  return children;
};

// Main App Component
function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;