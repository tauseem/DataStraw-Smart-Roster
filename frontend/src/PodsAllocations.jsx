import { useEffect, useState } from 'react'

const API = '/api'

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

const today = () => new Date().toISOString().slice(0, 10)

const emptyAllocation = {
  employee: '',
  brand_process: '',
  pod: '',
  allocation_start: '2026-01-01',
  allocation_end: '',
}

function PodsAndAllocations() {
  const [pods, setPods] = useState([])
  const [employees, setEmployees] = useState([])
  const [brands, setBrands] = useState([])
  const [processes, setProcesses] = useState([])
  const [brandProcesses, setBrandProcesses] = useState([])
  const [allocations, setAllocations] = useState([])
  const [form, setForm] = useState(emptyAllocation)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    const [p, e, b, pr, bp, a] = await Promise.all([
      request('/pods/'),
      request('/employees/'),
      request('/brands/'),
      request('/processes/'),
      request('/brand-processes/'),
      request('/employee-allocations/'),
    ])
    setPods(listOf(p))
    setEmployees(listOf(e))
    setBrands(listOf(b))
    setProcesses(listOf(pr))
    setBrandProcesses(listOf(bp))
    setAllocations(listOf(a))
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

  const activeEmployees = employees.filter((e) => e.employment_status === 'ACTIVE')

  const employeeLabel = (id) => {
    const found = employees.find((e) => e.id === id)
    return found ? `${found.employee_id} — ${found.full_name}` : `#${id}`
  }

  const brandProcessLabel = (id) => {
    const bp = brandProcesses.find((item) => item.id === id)
    if (!bp) return `#${id}`
    const brand = brands.find((b) => b.id === bp.brand)?.name || '?'
    const process = processes.find((p) => p.id === bp.process)?.name || '?'
    return `${brand} — ${process}`
  }

  const podName = (id) => pods.find((p) => p.id === id)?.name || '—'

  const setLead = (pod, leadId) => run(
    () => request(`/pods/${pod.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ lead: leadId }),
    }),
    `Lead updated for ${pod.name}.`
  )

  const saveAllocation = (event) => {
    event.preventDefault()
    run(
      () => request('/employee-allocations/', {
        method: 'POST',
        body: JSON.stringify({
          employee: Number(form.employee),
          brand_process: Number(form.brand_process),
          pod: form.pod ? Number(form.pod) : null,
          allocation_start: form.allocation_start,
          allocation_end: form.allocation_end || null,
          is_active: true,
        }),
      }).then(() => setForm(emptyAllocation)),
      'Allocation added.'
    )
  }

  const endAllocation = (allocation) => run(
    () => request(`/employee-allocations/${allocation.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ allocation_end: today() }),
    }),
    'Allocation ended today.'
  )

  const toggleAllocation = (allocation) => run(
    () => request(`/employee-allocations/${allocation.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !allocation.is_active }),
    }),
    `Allocation ${allocation.is_active ? 'deactivated' : 'activated'}.`
  )

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Pods and Allocations</h1>
          <p>Set pod leads and assign employees to brand-processes. Allocated employees are the ones the roster can use, and the ones it suggests as backups.</p>
        </div>
      </div>

      {message && <div className="toast toast-success" role="alert"><span>✓</span>{message}</div>}
      {error && <div className="toast toast-error" role="alert"><span>⚠</span>{error}</div>}

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Pods</h2><p>{pods.length} pods</p></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Pod</th><th>Code</th><th>Pod lead</th></tr>
            </thead>
            <tbody>
              {pods.map((pod) => (
                <tr key={pod.id}>
                  <td><strong>{pod.name}</strong></td>
                  <td>{pod.code}</td>
                  <td>
                    <select
                      value={pod.lead || ''}
                      onChange={(e) => setLead(pod, e.target.value ? Number(e.target.value) : null)}
                    >
                      <option value="">— No lead —</option>
                      {activeEmployees.map((e) => (
                        <option key={e.id} value={e.id}>{e.employee_id} — {e.full_name}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Add Allocation</h2>
            <p>Leave the end date empty for an open-ended allocation.</p>
          </div>
        </div>
        <form className="form-grid" onSubmit={saveAllocation}>
          <label>Employee
            <select required value={form.employee} onChange={(e) => setForm({ ...form, employee: e.target.value })}>
              <option value="">Select employee</option>
              {activeEmployees.map((e) => (
                <option key={e.id} value={e.id}>{e.employee_id} — {e.full_name}</option>
              ))}
            </select>
          </label>
          <label>Brand — Process
            <select required value={form.brand_process} onChange={(e) => setForm({ ...form, brand_process: e.target.value })}>
              <option value="">Select brand-process</option>
              {brandProcesses.map((bp) => (
                <option key={bp.id} value={bp.id}>{brandProcessLabel(bp.id)}</option>
              ))}
            </select>
          </label>
          <label>Pod
            <select value={form.pod} onChange={(e) => setForm({ ...form, pod: e.target.value })}>
              <option value="">No pod</option>
              {pods.map((pod) => (
                <option key={pod.id} value={pod.id}>{pod.name}</option>
              ))}
            </select>
          </label>
          <label>Start date
            <input type="date" required value={form.allocation_start} onChange={(e) => setForm({ ...form, allocation_start: e.target.value })} />
          </label>
          <label>End date
            <input type="date" value={form.allocation_end} onChange={(e) => setForm({ ...form, allocation_end: e.target.value })} />
          </label>
          <div className="form-submit">
            <button className="btn btn-primary">Add Allocation</button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Allocations</h2><p>{allocations.length} allocations</p></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Employee</th><th>Brand — Process</th><th>Pod</th><th>From</th><th>To</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {allocations.map((a) => (
                <tr key={a.id}>
                  <td>{employeeLabel(a.employee)}</td>
                  <td>{brandProcessLabel(a.brand_process)}</td>
                  <td>{podName(a.pod)}</td>
                  <td>{a.allocation_start}</td>
                  <td>{a.allocation_end || 'Open'}</td>
                  <td>{a.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <div className="table-actions">
                      <button className="text-btn" onClick={() => endAllocation(a)}>End today</button>
                      <button className="text-btn" onClick={() => toggleAllocation(a)}>
                        {a.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
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

export default PodsAndAllocations