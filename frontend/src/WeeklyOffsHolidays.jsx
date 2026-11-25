import { useEffect, useState } from 'react'

const API = '/api'

const WEEKDAYS = [
  [0, 'Monday'], [1, 'Tuesday'], [2, 'Wednesday'], [3, 'Thursday'],
  [4, 'Friday'], [5, 'Saturday'], [6, 'Sunday'],
]

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  const text = await response.text()
  const data = text ? JSON.parse(text) : {}

  if (!response.ok) {
    const message = Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
      .join(' | ')
    throw new Error(message || 'Request failed.')
  }

  return data
}

function listOf(data) {
  return Array.isArray(data) ? data : data.results || []
}

const emptyWeeklyOff = {
  employee: '',
  weekday: 6,
  effective_from: '2026-01-01',
  effective_until: '',
  is_active: true,
  is_preference: false,
}

const emptyHoliday = {
  name: '',
  holiday_date: '',
  region: 'IN',
  description: '',
  is_active: true,
}

function WeeklyOffsAndHolidays() {
  const [employees, setEmployees] = useState([])
  const [weeklyOffs, setWeeklyOffs] = useState([])
  const [holidays, setHolidays] = useState([])
  const [offForm, setOffForm] = useState(emptyWeeklyOff)
  const [holidayForm, setHolidayForm] = useState(emptyHoliday)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    const [e, w, h] = await Promise.all([
      request('/employees/'),
      request('/weekly-offs/'),
      request('/public-holidays/'),
    ])
    setEmployees(listOf(e))
    setWeeklyOffs(listOf(w))
    setHolidays(listOf(h))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const run = async (action, success) => {
    setError('')
    setMessage('')
    try {
      await action()
      await load()
      setMessage(success)
    } catch (err) {
      setError(err.message)
    }
  }

  const employeeLabel = (id) => {
    const found = employees.find((e) => e.id === id)
    return found ? `${found.employee_id} — ${found.full_name}` : `#${id}`
  }

  const saveWeeklyOff = (event) => {
    event.preventDefault()
    run(
      () => request('/weekly-offs/', {
        method: 'POST',
        body: JSON.stringify({
          employee: Number(offForm.employee),
          weekday: Number(offForm.weekday),
          effective_from: offForm.effective_from,
          effective_until: offForm.effective_until || null,
          is_active: true,
          is_preference: offForm.is_preference,
        }),
      }).then(() => setOffForm(emptyWeeklyOff)),
      offForm.is_preference ? 'Preferred weekly off added.' : 'Mandatory weekly off added.'
    )
  }

  const togglePreference = (off) => run(
    () => request(`/weekly-offs/${off.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_preference: !off.is_preference }),
    }),
    off.is_preference ? 'Changed to mandatory.' : 'Changed to preferred.'
  )

  const toggleOff = (off) => run(
    () => request(`/weekly-offs/${off.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !off.is_active }),
    }),
    `Weekly off ${off.is_active ? 'deactivated' : 'activated'}.`
  )

  const saveHoliday = (event) => {
    event.preventDefault()
    run(
      () => request('/public-holidays/', {
        method: 'POST',
        body: JSON.stringify(holidayForm),
      }).then(() => setHolidayForm(emptyHoliday)),
      'Public holiday added.'
    )
  }

  const toggleHoliday = (holiday) => run(
    () => request(`/public-holidays/${holiday.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !holiday.is_active }),
    }),
    `Holiday ${holiday.is_active ? 'deactivated' : 'activated'}.`
  )

  const activeEmployees = employees.filter((e) => e.employment_status === 'ACTIVE')

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Weekly Offs and Holidays</h1>
          <p>Mandatory offs are never overridden. Preferred offs give way when a brand-process needs cover, and each override is reported on the roster.</p>
        </div>
      </div>

      {message && <div className="toast toast-success" role="alert"><span>✓</span>{message}</div>}
      {error && <div className="toast toast-error" role="alert"><span>⚠</span>{error}</div>}

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Add Weekly Off</h2><p>Choose mandatory for a fixed off, or preferred if coverage can override it.</p></div>
        </div>
        <form className="form-grid" onSubmit={saveWeeklyOff}>
          <label>Employee
            <select required value={offForm.employee} onChange={(e) => setOffForm({ ...offForm, employee: e.target.value })}>
              <option value="">Select employee</option>
              {activeEmployees.map((e) => (
                <option key={e.id} value={e.id}>{e.employee_id} — {e.full_name}</option>
              ))}
            </select>
          </label>
          <label>Weekday
            <select value={offForm.weekday} onChange={(e) => setOffForm({ ...offForm, weekday: e.target.value })}>
              {WEEKDAYS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label>Type
            <select value={offForm.is_preference ? 'preferred' : 'mandatory'} onChange={(e) => setOffForm({ ...offForm, is_preference: e.target.value === 'preferred' })}>
              <option value="mandatory">Mandatory</option>
              <option value="preferred">Preferred</option>
            </select>
          </label>
          <label>Effective from
            <input type="date" required value={offForm.effective_from} onChange={(e) => setOffForm({ ...offForm, effective_from: e.target.value })} />
          </label>
          <label>Effective until
            <input type="date" value={offForm.effective_until} onChange={(e) => setOffForm({ ...offForm, effective_until: e.target.value })} />
          </label>
          <div className="form-submit">
            <button className="btn btn-primary">Add Weekly Off</button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Weekly Offs</h2><p>{weeklyOffs.length} records</p></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Employee</th><th>Day</th><th>Type</th><th>From</th><th>Until</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {weeklyOffs.map((off) => (
                <tr key={off.id}>
                  <td>{employeeLabel(off.employee)}</td>
                  <td>{WEEKDAYS.find(([v]) => v === off.weekday)?.[1] || off.weekday}</td>
                  <td>{off.is_preference ? 'Preferred' : 'Mandatory'}</td>
                  <td>{off.effective_from}</td>
                  <td>{off.effective_until || 'Open'}</td>
                  <td>{off.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <div className="table-actions">
                      <button className="text-btn" onClick={() => togglePreference(off)}>
                        Make {off.is_preference ? 'mandatory' : 'preferred'}
                      </button>
                      <button className="text-btn" onClick={() => toggleOff(off)}>
                        {off.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Public Holidays</h2><p>Brand-processes with holiday policy OFF do not run on these dates.</p></div>
        </div>
        <form className="form-grid" onSubmit={saveHoliday}>
          <label>Name
            <input required value={holidayForm.name} onChange={(e) => setHolidayForm({ ...holidayForm, name: e.target.value })} />
          </label>
          <label>Date
            <input type="date" required value={holidayForm.holiday_date} onChange={(e) => setHolidayForm({ ...holidayForm, holiday_date: e.target.value })} />
          </label>
          <label>Region
            <input required value={holidayForm.region} onChange={(e) => setHolidayForm({ ...holidayForm, region: e.target.value.toUpperCase() })} />
          </label>
          <div className="form-submit">
            <button className="btn btn-primary">Add Holiday</button>
          </div>
        </form>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Date</th><th>Name</th><th>Region</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {holidays.map((holiday) => (
                <tr key={holiday.id}>
                  <td>{holiday.holiday_date}</td>
                  <td>{holiday.name}</td>
                  <td>{holiday.region}</td>
                  <td>{holiday.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <button className="text-btn" onClick={() => toggleHoliday(holiday)}>
                      {holiday.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

export default WeeklyOffsAndHolidays