/**
 * Home Page
 *
 * Landing page / Dashboard entry point
 */

export default function HomePage() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          AI Ad Spend System
        </h1>
        <p className="text-gray-600 mb-8">
          Welcome to the AI Advertising Spend Management System.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Quick Stats Cards */}
          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-gray-500">Daily Reports</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">--</p>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-gray-500">Pending Topups</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">--</p>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-gray-500">Total Balance</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">--</p>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-gray-500">Reconciliations</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">--</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
