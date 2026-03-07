import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, TrendingUp, Plus, Activity, DollarSign, Calendar } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const COLORS = ['#8b5cf6', '#ec4899', '#10b981', '#3b82f6', '#f59e0b', '#6366f1'];

function App() {
  const [expenses, setExpenses] = useState([]);
  const [analytics, setAnalytics] = useState({ category_totals: {} });
  const [prediction, setPrediction] = useState(0);
  
  const [formData, setFormData] = useState({ amount: '', description: '', date: new Date().toISOString().split('T')[0], category: 'Miscellaneous' });
  const [isClassifying, setIsClassifying] = useState(false);
  const [smartAlert, setSmartAlert] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const expensesRes = await axios.get(`${API_BASE_URL}/expenses`);
      setExpenses(expensesRes.data);
      
      const analyticsRes = await axios.get(`${API_BASE_URL}/analytics`);
      setAnalytics(analyticsRes.data);
      
      const predictionRes = await axios.get(`${API_BASE_URL}/predict`);
      setPrediction(predictionRes.data.predicted_amount);
      
      // Smart Alert Logic (mocked threshold detection)
      if (analyticsRes.data.category_totals['Fuel'] > 4000) {
        setSmartAlert("Fuel spending is unusually high this month compared to the trend.");
      } else if (analyticsRes.data.category_totals['Maintenance'] > 1500) {
        setSmartAlert("Maintenance costs have spiked recently.");
      } else {
        setSmartAlert(null);
      }
    } catch (error) {
      console.error("Failed to fetch data", error);
    }
  };

  const classifyDescription = async (desc) => {
    if (desc.trim() === '') return;
    setIsClassifying(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/classify`, { description: desc });
      setFormData(prev => ({ ...prev, category: res.data.category }));
    } catch (error) {
      console.error("Classification failed", error);
    }
    setIsClassifying(false);
  };

  const handleDescChange = (e) => {
    const val = e.target.value;
    setFormData(prev => ({ ...prev, description: val }));
  };

  const handleDescBlur = () => {
    classifyDescription(formData.description);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/expenses`, {
        ...formData,
        amount: parseFloat(formData.amount)
      });
      setFormData({ amount: '', description: '', date: new Date().toISOString().split('T')[0], category: 'Miscellaneous' });
      fetchData();
    } catch (error) {
      console.error("Failed to add expense", error);
    }
  };

  // Prepare chart data
  const categoryData = Object.keys(analytics.category_totals).map(key => ({
    name: key,
    value: analytics.category_totals[key]
  }));

  // Aggregate recent daily expenses for line chart
  const recentDays = {};
  expenses.slice(0, 30).forEach(e => {
    recentDays[e.date] = (recentDays[e.date] || 0) + e.amount;
  });
  
  const lineChartData = Object.keys(recentDays).sort().map(d => ({
    date: d.slice(5), // MM-DD
    amount: recentDays[d]
  }));

  const totalExpense = expenses.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="app-container animate-fade-in">
      <header className="header">
        <div className="logo">
          <Activity size={32} color="#8b5cf6" />
          Smart Expense Analyzer
        </div>
      </header>

      {smartAlert && (
        <div className="smart-alert">
          <AlertCircle className="smart-alert-icon" size={24} />
          <div className="smart-alert-content">
            <h4>Smart Alert Detected</h4>
            <p>{smartAlert}</p>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Entry Form */}
        <div className="glass-panel col-span-4 stagger-1">
          <h3>Add New Expense</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Date</label>
              <input type="date" className="form-input" 
                value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} required />
            </div>
            
            <div className="form-group">
              <label className="form-label">Amount (₹)</label>
              <input type="number" step="0.01" className="form-input" placeholder="e.g. 500"
                value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} required />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <input type="text" className="form-input" placeholder="e.g. Van diesel"
                value={formData.description} 
                onChange={handleDescChange}
                onBlur={handleDescBlur}
                required />
            </div>

            <div className="form-group">
              <label className="form-label">
                AI Suggested Category {isClassifying && <span style={{color: 'var(--accent-primary)', fontSize: '0.8rem'}}> (Classifying...)</span>}
              </label>
              <select className="form-input" value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})}>
                <option value="Fuel">Fuel</option>
                <option value="Salary">Salary</option>
                <option value="Maintenance">Maintenance</option>
                <option value="Rent">Rent</option>
                <option value="Utilities">Utilities</option>
                <option value="Miscellaneous">Miscellaneous</option>
              </select>
            </div>

            <button type="submit" className="btn w-100" style={{width: '100%'}}>
              <Plus size={18} /> Add Expense
            </button>
          </form>
        </div>

        {/* Top KPIs */}
        <div className="col-span-8 dashboard-grid">
          <div className="glass-panel col-span-6 stagger-2" style={{display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
            <h4 style={{color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <DollarSign size={18} /> Total Recorded Expense
            </h4>
            <div style={{fontSize: '2.5rem', fontWeight: '700', color: 'white'}}>
              ₹{totalExpense.toLocaleString(undefined, {minimumFractionDigits: 2})}
            </div>
          </div>
          
          <div className="glass-panel col-span-6 stagger-2" style={{display: 'flex', flexDirection: 'column', justifyContent: 'center', background: 'rgba(139, 92, 246, 0.1)'}}>
            <h4 style={{color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap'}}>
              <TrendingUp size={18} color="var(--accent-primary)"/> AI Prediction: Next Month
            </h4>
            <div style={{fontSize: prediction === 0 ? '1rem' : '2.5rem', fontWeight: '700', color: '#c4b5fd'}}>
              {prediction > 0 ? `₹${prediction.toLocaleString(undefined, {minimumFractionDigits: 2})}` : 'Need more monthly data for trend prediction'}
            </div>
          </div>

          <div className="glass-panel col-span-12 stagger-3">
             <h3 style={{marginBottom: '1rem'}}>Category Breakdown</h3>
             <div style={{height: 250}}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{backgroundColor: '#0d0e15', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px'}}/>
                  <Bar dataKey="value" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
             </div>
          </div>
        </div>

        {/* All Transactions List */}
        <div className="glass-panel col-span-8 stagger-3">
          <h3>All Transactions</h3>
          <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '10px' }}>
            <ul className="expense-list">
              {expenses.map((e) => (
                <li key={e.id} className="expense-item">
                  <div className="expense-details">
                    <span className="expense-title">{e.description || 'Unknown'}</span>
                    <span className="expense-meta">
                      <Calendar size={14} /> {e.date}
                      <span className="badge badge-violet" style={{marginLeft: '0.5rem'}}>{e.category}</span>
                    </span>
                  </div>
                  <div className="expense-amount">₹{e.amount.toFixed(2)}</div>
                </li>
              ))}
              {expenses.length === 0 && <p>No expenses recorded yet.</p>}
            </ul>
          </div>
        </div>
        
        {/* Trend Chart */}
        <div className="glass-panel col-span-4 stagger-3">
          <h3>Recent Trend</h3>
           <div style={{height: 250, marginTop: '1rem'}}>
             {lineChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineChartData.slice(-14)}>
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={{backgroundColor: '#0d0e15', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px'}}/>
                    <Line type="monotone" dataKey="amount" stroke="var(--accent-secondary)" strokeWidth={3} dot={false}/>
                  </LineChart>
                </ResponsiveContainer>
             ) : <p style={{marginTop: '2rem'}}>Not enough data points.</p>}
           </div>
        </div>

      </div>
    </div>
  );
}

export default App;
