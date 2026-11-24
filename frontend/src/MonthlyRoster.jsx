
import { useCallback, useEffect, useState } from 'react'

const INITIAL_YEAR = 2026
const INITIAL_MONTH = 12

const VIEWS = [
  ['company', 'Company'],
  ['pods', 'Pods'],
  ['brands', 'Brands'],
  ['processes', 'Processes'],
  ['coverage', 'Coverage'],
  ['employees', 'Employees'],
]

// API request helper
async function requestMonth(method, year, month) {
  const response = await fetch(
    method === 'POST'
      ? '/api/monthly-roster/'
      : `/api/monthly-roster/?year=${year}&month=${month}`,
    method === 'POST'
      ? {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            year: Number(year),
            month: Number(month),
          }),
        }
      : {}
  )

  const result = await response.json()

  if (!response.ok) {
    throw new Error(result.message || 'Request failed.')
  }

  return result
}

function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
  })
}

function summarizeByEmployee(rows = []) {
  const map = {}

  rows.forEach((row) => {
    if (!map[row.employee_id]) {
      map[row.employee_id] = {
        employee_id: row.employee_id,
        employee: row.employee,
        pod: row.pod,
        brand: row.brand,
        process: row.process,
        days: 0,
      }
    }

    map[row.employee_id].days += 1
  })

  return Object.values(map).sort((a, b) =>
    a.employee_id.localeCompare(b.employee_id)
  )
}

// Employee table
function EmployeeTable({ rows }) {
  if (!rows.length) {
    return <div className="empty-state">No assignments.</div>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Employee</th>
            <th>ID</th>
            <th>Pod</th>
            <th>Brand</th>
            <th>Process</th>
            <th>Days worked</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row.employee_id}>
              <td><strong>{row.employee}</strong></td>
              <td>{row.employee_id}</td>
              <td>{row.pod}</td>
              <td>{row.brand}</td>
              <td>{row.process}</td>
              <td>{row.days}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Company view
function CompanyView({ data }) {
  const days = Object.entries(data.company)

  if (!days.length) {
    return (
      <div className="empty-state">
        No assignments this month. Generate the month first.
      </div>
    )
  }

  return days.map(([day, rows]) => (
    <section className="panel" key={day}>
      <details>
        <summary>
          <strong>{formatDate(day)}</strong> — {rows.length} working
        </summary>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Pod</th>
                <th>Brand</th>
                <th>Process</th>
                <th>Shift</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr key={row.assignment_id}>
                  <td>{row.employee}</td>
                  <td>{row.pod}</td>
                  <td>{row.brand}</td>
                  <td>{row.process}</td>
                  <td>{row.shift}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  ))
}

// Pods view
function PodsView({ data }) {
  const pods = Object.entries(data.pods)

  if (!pods.length) {
    return <div className="empty-state">No assignments this month.</div>
  }

  return pods.map(([pod, rows]) => (
    <section className="panel" key={pod}>
      <div className="panel-heading">
        <div>
          <h2>{pod}</h2>
          <p>Lead: {data.pod_leads?.[pod] || 'Not set'}</p>
        </div>
      </div>

      <EmployeeTable rows={summarizeByEmployee(rows)} />
    </section>
  ))
}

// Brands view
function BrandsView({ data }) {
  const brands = Object.keys(data.brand_coverage).sort()

  if (!brands.length) {
    return <div className="empty-state">No brands configured.</div>
  }

  return brands.map((brand) => (
    <section className="panel" key={brand}>
      <div className="panel-heading">
        <div>
          <h2>{brand}</h2>
          <p>Assigned employees and daily coverage</p>
        </div>
      </div>

      <EmployeeTable
        rows={summarizeByEmployee(data.brands[brand] || [])}
      />

      <details className="details-block">
        <summary>
          Daily coverage ({data.brand_coverage[brand].length} slots)
        </summary>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Process</th>
                <th>Required</th>
                <th>Assigned</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {data.brand_coverage[brand].map((item, index) => (
                <tr key={index}>
                  <td>{formatDate(item.date)}</td>
                  <td>{item.process}</td>
                  <td>{item.required}</td>
                  <td>{item.assigned}</td>
                  <td>
                    <span className={`status-badge status-${item.status.toLowerCase()}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  ))
}

// Processes view
function ProcessesView({ data }) {
  const processes = Object.entries(data.processes)

  if (!processes.length) {
    return <div className="empty-state">No assignments this month.</div>
  }

  return processes.map(([process, rows]) => (
    <section className="panel" key={process}>
      <div className="panel-heading">
        <div>
          <h2>{process}</h2>
          <p>Staff and working days for this process</p>
        </div>
      </div>

      <EmployeeTable rows={summarizeByEmployee(rows)} />
    </section>
  ))
}

// Coverage view
function CoverageView({ data, shortOnly, setShortOnly }) {
  const items = data.coverage.filter((item) =>
    shortOnly ? item.status === 'SHORT' : true
  )

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Coverage</h2>
          <p>Required versus assigned on each working day</p>
        </div>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={shortOnly}
            onChange={(e) => setShortOnly(e.target.checked)}
          />
          {' '}Show shortages only
        </label>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          No matching coverage slots.
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Brand</th>
                <th>Process</th>
                <th>Required</th>
                <th>Assigned</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  <td>{formatDate(item.date)}</td>
                  <td>{item.brand}</td>
                  <td>{item.process}</td>
                  <td>{item.required}</td>
                  <td>{item.assigned}</td>
                  <td>
                    <span className={`status-badge status-${item.status.toLowerCase()}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

// Employees view
function EmployeesView({
  data,
  selectedEmployee,
  setSelectedEmployee,
}) {
  const employees = data.employees || []

  const current =
    employees.find(
      (item) => item.employee_id === selectedEmployee
    ) || employees[0]

  if (!current) {
    return <div className="empty-state">No employees found.</div>
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>{current.employee}</h2>
          <p>
            Weekly off:{' '}
            {current.weekly_offs.length
              ? current.weekly_offs.join(', ')
              : 'None'}
          </p>
        </div>

        <select
          value={current.employee_id}
          onChange={(e) => setSelectedEmployee(e.target.value)}
        >
          {employees.map((item) => (
            <option
              key={item.employee_id}
              value={item.employee_id}
            >
              {item.employee_id} — {item.employee}
            </option>
          ))}
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Status</th>
              <th>Detail</th>
            </tr>
          </thead>

          <tbody>
            {current.calendar.map((day) => (
              <tr key={day.date}>
                <td>{formatDate(day.date)}</td>
                <td>{day.status}</td>
                <td>{day.detail || '--'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// Main Monthly Roster component
export default function MonthlyRoster() {
  const [year, setYear] = useState(INITIAL_YEAR)
  const [month, setMonth] = useState(INITIAL_MONTH)
  const [view, setView] = useState('company')
  const [data, setData] = useState(null)
  const [selectedEmployee, setSelectedEmployee] = useState('')
  const [shortOnly, setShortOnly] = useState(false)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  // Manual load and generation
  const fetchMonth = useCallback(async (method) => {
    setBusy(true)
    setError('')
    setMessage('')

    try {
      const result = await requestMonth(method, year, month)

      setData(result)

      if (result.generation) {
        setMessage(
          `Generated ${result.generation.days} days. ${result.generation.days_with_issues} day(s) have shortages or conflicts.`
        )
      }
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }, [year, month])

  // Initial roster loading
  useEffect(() => {
    let cancelled = false

    async function loadInitialMonth() {
      try {
        const result = await requestMonth(
          'GET',
          INITIAL_YEAR,
          INITIAL_MONTH
        )

        if (!cancelled) {
          setData(result)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load monthly roster.')
        }
      } finally {
        if (!cancelled) {
          setBusy(false)
        }
      }
    }

    loadInitialMonth()

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Monthly Roster</h1>
          <p>
            Company, pod, brand, process, coverage, and employee views for the month.
          </p>
        </div>
      </div>

      <section className="panel">
        <div className="roster-toolbar">
          <label>
            Year
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
          </label>

          <label>
            Month
            <input
              type="number"
              min="1"
              max="12"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
            />
          </label>

          <button
            className="btn btn-secondary"
            onClick={() => fetchMonth('GET')}
            disabled={busy}
          >
            Load Month
          </button>

          <button
            className="btn btn-primary"
            onClick={() => fetchMonth('POST')}
            disabled={busy}
          >
            {busy ? 'Working...' : 'Generate Whole Month'}
          </button>
        </div>

        {message && <p>{message}</p>}

        {error && (
          <div className="alert alert-warning">
            {error}
          </div>
        )}
      </section>

      {!data ? (
        <div className="empty-state">
          {error ? 'Unable to load monthly roster.' : 'Loading monthly roster...'}
        </div>
      ) : (
        <>
          <div className="stats-grid compact-stats">
            <div className="stat-card">
              <div className="stat-card-top">
                <span>Assignments</span>
              </div>
              <div className="stat-value">
                {data.summary.assignments}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-card-top">
                <span>Working slots</span>
              </div>
              <div className="stat-value">
                {data.summary.working_slots}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-card-top">
                <span>Short slots</span>
              </div>
              <div className="stat-value">
                {data.summary.short_slots}
              </div>
            </div>
          </div>

          <div className="roster-toolbar">
            {VIEWS.map(([key, label]) => (
              <button
                key={key}
                className={`btn ${view === key ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setView(key)}
              >
                {label}
              </button>
            ))}
          </div>

          {view === 'company' && (
            <CompanyView data={data} />
          )}

          {view === 'pods' && (
            <PodsView data={data} />
          )}

          {view === 'brands' && (
            <BrandsView data={data} />
          )}

          {view === 'processes' && (
            <ProcessesView data={data} />
          )}

          {view === 'coverage' && (
            <CoverageView
              data={data}
              shortOnly={shortOnly}
              setShortOnly={setShortOnly}
            />
          )}

          {view === 'employees' && (
            <EmployeesView
              data={data}
              selectedEmployee={selectedEmployee}
              setSelectedEmployee={setSelectedEmployee}
            />
          )}
        </>
      )}
    </>
  )
}
