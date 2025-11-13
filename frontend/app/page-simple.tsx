"use client";

import React, { useState, useEffect } from "react";

export default function SimpleHomePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 测试API连接
    fetch('http://localhost:8001/api/v1/projects')
      .then(response => response.json())
      .then(result => {
        console.log('API响应:', result);
        setData(result);
        setLoading(false);
      })
      .catch(err => {
        console.error('API错误:', err);
        setError('API连接失败');
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
          AI广告代投系统
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">总预算</h3>
            <p className="text-2xl font-bold">¥125,000</p>
            <p className="text-green-400 text-sm">↑ 12.5%</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">活跃项目</h3>
            <p className="text-2xl font-bold">24</p>
            <p className="text-green-400 text-sm">↑ 8.2%</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">转化率</h3>
            <p className="text-2xl font-bold">3.8%</p>
            <p className="text-red-400 text-sm">↓ 2.1%</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">AI评分</h3>
            <p className="text-2xl font-bold">92</p>
            <p className="text-green-400 text-sm">↑ 5.8%</p>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
          <h2 className="text-2xl font-bold mb-4">API测试结果</h2>
          {loading ? (
            <p>正在加载API数据...</p>
          ) : error ? (
            <div className="text-red-400">
              <p>错误: {error}</p>
              <p>请确保后端服务正在运行在 http://localhost:8001</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-900/20 p-4 rounded-lg border border-green-700">
                <p className="text-green-400">✅ API连接成功</p>
                <p className="text-sm text-gray-400 mt-2">返回数据: {JSON.stringify(data?.data?.items?.length || 0)} 个项目</p>
              </div>

              {data?.data?.items?.map((project: any, index: number) => (
                <div key={index} className="bg-gray-700 p-4 rounded-lg">
                  <h3 className="font-semibold">{project.name}</h3>
                  <p className="text-sm text-gray-400">预算: ${project.budget.toLocaleString()}</p>
                  <p className="text-sm text-gray-400">状态: {project.status}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => window.location.href = 'http://localhost:8001/docs'}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium transition-colors"
          >
            查看API文档
          </button>
        </div>
      </div>
    </div>
  );
}