
import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API = '/api'
function friendlyError(message) {
  const text = String(message || '').toLowerCase()

  if (
    text.includes('non_field_errors') &&
    text.includes('employee') &&
    text.includes('shift_date')
  ) {
    return 'This employee is already assigned to a shift on this date. Please select another employee or date.'
  }

  if (text.includes('approved leave') || (text.includes('leave') && text.includes('assignment'))) {
    return 'This employee has approved leave for the selected date. Assignment is not allowed.'
  }

  if (text.includes('inactive')) {
    return 'This employee is inactive and cannot be assigned.'
  }

  if (text.includes('overlap')) {
    return 'This employee already has an overlapping shift. Please select another shift.'
  }

  return String(message || 'Something went wrong. Please try again.')
}
const today = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const emptyEmployee = {
  employee_id: '',
  full_name: '',
  email: '',
  phone: '',
  brand: '',
  process: '',
  employment_status: 'ACTIVE',
  joining_date: today(),
}

const emptyShift = {
  shift_name: '',
  shift_code: '',
  shift_type: 'MORNING',
  start_time: '09:00',
  end_time: '18:00',
  break_duration: 60,
  is_active: true,
}

const emptyRequirement = {
  shift: '',
  requirement_date: today(),
  required_employees: 1,
}

const emptyLeave = {
  employee: '',
  start_date: today(),
  end_date: today(),
  reason: '',
  status: 'PENDING',
}

async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  const text = await response.text()
    let data

  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { detail: text }
  }

  if (!response.ok) {
    const message =
      data.detail ||
      data.message ||
      Object.entries(data)
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : JSON.stringify(value)}`)
        .join(' | ') ||
      'Something went wrong.'

    throw new Error(message)
  }

  return data
}

function getList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data.results)) return data.results
  return []
}

function formatTime(value) {
  if (!value) return '--'
  return value.slice(0, 5)
}

function formatDate(value) {
  if (!value) return '--'
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function StatCard({ label, value, note, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <div className="stat-value">{value ?? 0}</div>
      {note && <div className="stat-note">{note}</div>}
    </div>
  )
}

function StatusBadge({ value }) {
  const normalized = String(value || '').toLowerCase().replaceAll('_', '-')
  return <span className={`status-badge status-${normalized}`}>{value || 'Unknown'}</span>
}

function EmptyState({ children = 'No records found.' }) {
  return <div className="empty-state">{children}</div>
}

function PageHeader({ title, description, action }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  )
}

export default function App() {
  const [activePage, setActivePage] = useState('Dashboard')

  const [employees, setEmployees] = useState([])
  const [shifts, setShifts] = useState([])
  const [assignments, setAssignments] = useState([])
  const [requirements, setRequirements] = useState([])
  const [leaves, setLeaves] = useState([])
  const [attendance, setAttendance] = useState([])
  const [summary, setSummary] = useState(null)

  const [selectedDate, setSelectedDate] = useState(today())
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)

  const [pageNotices, setPageNotices] = useState({})
  const [generationResult, setGenerationResult] = useState(null)

  const [employeeForm, setEmployeeForm] = useState(emptyEmployee)
  const [shiftForm, setShiftForm] = useState(emptyShift)
  const [requirementForm, setRequirementForm] = useState(emptyRequirement)
  const [leaveForm, setLeaveForm] = useState(emptyLeave)

  const [editingEmployee, setEditingEmployee] = useState(null)
  const [editingShift, setEditingShift] = useState(null)
  const [editingAssignment, setEditingAssignment] = useState(null)

  const [searchEmployee, setSearchEmployee] = useState('')
  const [employeeModal, setEmployeeModal] = useState(false)
  const [shiftModal, setShiftModal] = useState(false)
  const [leaveModal, setLeaveModal] = useState(false)
  const [assignmentModal, setAssignmentModal] = useState(false)

  const [attendanceForm, setAttendanceForm] = useState({
    assignment: '',
    status: 'PRESENT',
    check_in: '',
    check_out: '',
    notes: '',
  })

  const notify = (text) => {
  const page = activePage

  setPageNotices((previous) => ({
    ...previous,
    [page]: { type: 'success', text },
  }))

  window.setTimeout(() => {
    setPageNotices((previous) => {
      if (previous[page]?.text !== text) return previous

      const updated = { ...previous }
      delete updated[page]
      return updated
    })
  }, 5000)
}

const notifyError = useCallback((text) => {
  setPageNotices((previous) => ({
    ...previous,
    [activePage]: {
      type: 'error',
      text: friendlyError(text),
    },
  }))
}, [activePage])

  const loadEmployees = useCallback(async () => {
    const data = await apiRequest('/employees/')
    setEmployees(getList(data))
  }, [])

  const loadShifts = useCallback(async () => {
    const data = await apiRequest('/shifts/')
    setShifts(getList(data))
  }, [])

  const loadAssignments = useCallback(async (dateValue = selectedDate) => {
    const data = await apiRequest(`/roster-calendar/?date=${dateValue}`)
    setAssignments(data.assignments || [])
  }, [selectedDate])

  const loadRequirements = useCallback(async () => {
    const data = await apiRequest('/staffing-requirements/')
    setRequirements(getList(data))
  }, [])

  const loadLeaves = useCallback(async () => {
    const data = await apiRequest('/leave-requests/')
    setLeaves(getList(data))
  }, [])

  const loadAttendance = useCallback(async () => {
    const data = await apiRequest('/attendance/')
    setAttendance(getList(data))
  }, [])

  const loadSummary = useCallback(async () => {
    const data = await apiRequest('/dashboard-summary/')
    setSummary(data)
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadEmployees(),
        loadShifts(),
        loadAssignments(),
        loadRequirements(),
        loadLeaves(),
        loadAttendance(),
        loadSummary(),
      ])
    } catch (err) {
      notifyError(err.message)
    } finally {
      setLoading(false)
    }
  }, [
    loadEmployees,
    loadShifts,
    loadAssignments,
    loadRequirements,
    loadLeaves,
    loadAttendance,
    loadSummary,
    notifyError
  ])

   useEffect(() => {
    const task = Promise.resolve().then(() => loadAll())

    return () => {
      task.catch(() => {})
    }
  }, [loadAll])

  useEffect(() => {
    const task = Promise.resolve().then(() => loadAssignments(selectedDate))

    task.catch((err) => notifyError(err.message))
  }, [selectedDate, loadAssignments, notifyError])

  const refreshPage = async () => {
    try {
      await loadAll()
      notify('Data refreshed.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // NAVIGATION
  // -----------------------------------------

  const navigation = [
    { name: 'Dashboard', icon: '▦', section: 'OVERVIEW' },
    { name: 'Employees', icon: '♙', section: 'WORKFORCE' },
    { name: 'Shifts', icon: '◷', section: 'WORKFORCE' },
    { name: 'Staffing', icon: '▤', section: 'WORKFORCE' },
    { name: 'Roster', icon: '▦', section: 'SCHEDULING' },
    { name: 'Leave Management', icon: '▧', section: 'SCHEDULING' },
    { name: 'Attendance', icon: '✓', section: 'SCHEDULING' },
  ]

  // -----------------------------------------
  // EMPLOYEE CRUD
  // -----------------------------------------

  const openEmployeeForm = (employee = null) => {
    setEditingEmployee(employee)
    setEmployeeForm(employee ? {
      employee_id: employee.employee_id || '',
      full_name: employee.full_name || '',
      email: employee.email || '',
      phone: employee.phone || '',
      brand: employee.brand || '',
      process: employee.process || '',
      employment_status: employee.employment_status || 'ACTIVE',
      joining_date: employee.joining_date || today(),
    } : emptyEmployee)
    setEmployeeModal(true)
  }

  const saveEmployee = async (event) => {
    event.preventDefault()
    setSaving(true)

    try {
      const endpoint = editingEmployee
        ? `/employees/${editingEmployee.id}/`
        : '/employees/'

      await apiRequest(endpoint, {
        method: editingEmployee ? 'PUT' : 'POST',
        body: JSON.stringify(employeeForm),
      })

      setEmployeeModal(false)
      setEditingEmployee(null)
      setEmployeeForm(emptyEmployee)
      await loadEmployees()
      await loadSummary()
      notify(editingEmployee ? 'Employee updated.' : 'Employee created.')
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const toggleEmployee = async (employee) => {
    const updated = {
      ...employee,
      employment_status: employee.employment_status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE',
    }

    try {
      await apiRequest(`/employees/${employee.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ employment_status: updated.employment_status }),
      })
      await loadEmployees()
      await loadSummary()
      notify('Employee status updated.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  const deleteEmployee = async (employee) => {
    if (!window.confirm(`Delete ${employee.full_name}?`)) return

    try {
      await apiRequest(`/employees/${employee.id}/`, { method: 'DELETE' })
      await loadEmployees()
      await loadSummary()
      notify('Employee deleted.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // SHIFT CRUD
  // -----------------------------------------

  const openShiftForm = (shift = null) => {
    setEditingShift(shift)
    setShiftForm(shift ? {
      shift_name: shift.shift_name || '',
      shift_code: shift.shift_code || '',
      shift_type: shift.shift_type || 'MORNING',
      start_time: formatTime(shift.start_time),
      end_time: formatTime(shift.end_time),
      break_duration: shift.break_duration ?? 60,
      is_active: shift.is_active ?? true,
    } : emptyShift)
    setShiftModal(true)
  }

  const saveShift = async (event) => {
    event.preventDefault()
    setSaving(true)

    try {
      const endpoint = editingShift ? `/shifts/${editingShift.id}/` : '/shifts/'

      await apiRequest(endpoint, {
        method: editingShift ? 'PUT' : 'POST',
        body: JSON.stringify(shiftForm),
      })

      setShiftModal(false)
      setEditingShift(null)
      setShiftForm(emptyShift)
      await loadShifts()
      await loadSummary()
      notify(editingShift ? 'Shift updated.' : 'Shift created.')
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const toggleShift = async (shift) => {
    try {
      await apiRequest(`/shifts/${shift.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !shift.is_active }),
      })
      await loadShifts()
      await loadSummary()
      notify('Shift status updated.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // STAFFING REQUIREMENTS
  // -----------------------------------------

  const saveRequirement = async (event) => {
    event.preventDefault()
    setSaving(true)

    try {
      await apiRequest('/staffing-requirements/', {
        method: 'POST',
        body: JSON.stringify({
          ...requirementForm,
          shift: Number(requirementForm.shift),
          required_employees: Number(requirementForm.required_employees),
        }),
      })

      setRequirementForm(emptyRequirement)
      await loadRequirements()
      notify('Staffing requirement saved.')
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const deleteRequirement = async (item) => {
    if (!window.confirm('Delete this staffing requirement?')) return

    try {
      await apiRequest(`/staffing-requirements/${item.id}/`, { method: 'DELETE' })
      await loadRequirements()
      notify('Staffing requirement deleted.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // ROSTER GENERATION
  // -----------------------------------------

  const generateRoster = async () => {
    if (!selectedDate) {
      notifyError('Choose a roster date first.')
      return
    }

    if (!window.confirm(`Generate roster for ${formatDate(selectedDate)}?`)) return

    setGenerating(true)
    setGenerationResult(null)

    try {
      const result = await apiRequest('/generate-roster/', {
        method: 'POST',
        body: JSON.stringify({ date: selectedDate }),
      })

      setGenerationResult(result)
      await loadAssignments(selectedDate)
      await loadSummary()

      if (result.success) {
        notify('Roster generated successfully.')
      } else {
        notify('Roster generated with staffing shortages. Check the results.')
      }
    } catch (err) {
      notifyError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  // -----------------------------------------
  // MANUAL ROSTER ASSIGNMENT
  // -----------------------------------------

  const openAssignmentForm = (assignment = null) => {
    setEditingAssignment(assignment)
    setAssignmentModal(true)
  }

  
  const saveAssignment = async (event) => {
    event.preventDefault()
    setSaving(true)

    const form = event.currentTarget
    const formData = new FormData(form)

    const payload = {
      employee: Number(formData.get('employee')),
      shift: Number(formData.get('shift')),
      shift_date: selectedDate,
      status: formData.get('status') || 'SCHEDULED',
    }

    // Check approved leave before submitting the assignment.
    const employeeOnLeave = leaves.find((leave) => {
      const leaveEmployeeId = leave.employee?.id ?? leave.employee

      return (
        String(leaveEmployeeId) === String(payload.employee) &&
        leave.status === 'APPROVED' &&
        leave.start_date <= selectedDate &&
        leave.end_date >= selectedDate
      )
    })

    if (employeeOnLeave) {
      const employee = employees.find(
        (item) => String(item.id) === String(payload.employee)
      )

      setSaving(false)

      notifyError(
        `${employee?.full_name || 'This employee'} has approved leave from ${formatDate(employeeOnLeave.start_date)} to ${formatDate(employeeOnLeave.end_date)}. Assignment is not allowed.`
      )

      return
    }

    try {
      const endpoint = editingAssignment
        ? `/assignments/${editingAssignment.id}/`
        : '/assignments/'

      await apiRequest(endpoint, {
        method: editingAssignment ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      })

      setAssignmentModal(false)
      setEditingAssignment(null)

      await loadAssignments(selectedDate)
      await loadSummary()

      notify(
        editingAssignment
          ? 'Assignment updated.'
          : 'Employee assigned.'
      )
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }


  const cancelAssignment = async (assignment) => {
    if (!window.confirm(`Cancel assignment for ${assignment.employee_name}?`)) return

    try {
      await apiRequest(`/assignments/${assignment.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'CANCELLED' }),
      })
      await loadAssignments(selectedDate)
      await loadSummary()
      notify('Assignment cancelled.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // LEAVE MANAGEMENT
  // -----------------------------------------

  const saveLeave = async (event) => {
    event.preventDefault()
    setSaving(true)

    try {
      await apiRequest('/leave-requests/', {
        method: 'POST',
        body: JSON.stringify({
          ...leaveForm,
          employee: Number(leaveForm.employee),
        }),
      })

      setLeaveModal(false)
      setLeaveForm(emptyLeave)
      await loadLeaves()
      await loadSummary()
      notify('Leave request submitted.')
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const updateLeaveStatus = async (leave, newStatus) => {
    const action = newStatus === 'APPROVED' ? 'approve' : 'reject'

    if (!window.confirm(`${action === 'approve' ? 'Approve' : 'Reject'} this leave request?`)) return

    try {
      await apiRequest(`/leave-requests/${leave.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      })
      await loadLeaves()
      await loadSummary()
      notify(`Leave request ${newStatus.toLowerCase()}.`)
    } catch (err) {
      notifyError(err.message)
    }
  }

  const deleteLeave = async (leave) => {
    if (!window.confirm('Delete this leave request?')) return

    try {
      await apiRequest(`/leave-requests/${leave.id}/`, { method: 'DELETE' })
      await loadLeaves()
      await loadSummary()
      notify('Leave request deleted.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // ATTENDANCE
  // -----------------------------------------

  const saveAttendance = async (event) => {
    event.preventDefault()
    setSaving(true)

    const payload = {
      ...attendanceForm,
      assignment: Number(attendanceForm.assignment),
      check_in: attendanceForm.check_in || null,
      check_out: attendanceForm.check_out || null,
    }

    try {
      await apiRequest('/attendance/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      setAttendanceForm({
        assignment: '',
        status: 'PRESENT',
        check_in: '',
        check_out: '',
        notes: '',
      })

      await loadAttendance()
      await loadSummary()
      notify('Attendance recorded.')
    } catch (err) {
      notifyError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const deleteAttendance = async (item) => {
    if (!window.confirm('Delete this attendance record?')) return

    try {
      await apiRequest(`/attendance/${item.id}/`, { method: 'DELETE' })
      await loadAttendance()
      await loadSummary()
      notify('Attendance record deleted.')
    } catch (err) {
      notifyError(err.message)
    }
  }

  // -----------------------------------------
  // FILTERS AND DERIVED DATA
  // -----------------------------------------

  const filteredEmployees = employees.filter((employee) => {
    const term = searchEmployee.toLowerCase()
    return (
      employee.full_name?.toLowerCase().includes(term) ||
      employee.employee_id?.toLowerCase().includes(term) ||
      employee.email?.toLowerCase().includes(term) ||
      employee.process?.toLowerCase().includes(term) ||
      employee.brand?.toLowerCase().includes(term)
    )
  })

  const activeEmployees = employees.filter(
    (employee) => employee.employment_status === 'ACTIVE'
  )

  const activeShifts = shifts.filter((shift) => shift.is_active)

  const pendingLeaves = leaves.filter((leave) => leave.status === 'PENDING')

  const presentCount = attendance.filter((item) => item.status === 'PRESENT').length
  const absentCount = attendance.filter((item) => item.status === 'ABSENT').length

  // -----------------------------------------
  // DASHBOARD
  // -----------------------------------------

  const renderDashboard = () => (
    <>
      <PageHeader
        title="Dashboard"
        description="Your workforce and roster operations at a glance."
        action={<button className="btn btn-primary" onClick={refreshPage}>↻ Refresh</button>}
      />

      <div className="stats-grid">
        <StatCard
          label="Total Employees"
          value={summary?.employees?.total ?? employees.length}
          note="Registered workforce"
          icon="♙"
        />
        <StatCard
          label="Active Employees"
          value={summary?.employees?.active ?? activeEmployees.length}
          note="Available workforce"
          icon="✓"
        />
        <StatCard
          label="Active Shifts"
          value={summary?.shifts?.active ?? activeShifts.length}
          note="Configured shifts"
          icon="◷"
        />
        <StatCard
          label="Today's Assignments"
          value={summary?.roster?.today_assignments ?? 0}
          note="Non-cancelled assignments"
          icon="▦"
        />
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Workforce Overview</h2>
              <p>Employee status distribution</p>
            </div>
          </div>
          <div className="overview-list">
            <div className="overview-row">
              <span>Active employees</span>
              <strong>{summary?.employees?.active ?? activeEmployees.length}</strong>
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${employees.length ? ((summary?.employees?.active ?? activeEmployees.length) / employees.length) * 100 : 0}%`,
                }}
              />
            </div>
            <div className="overview-row">
              <span>Inactive employees</span>
              <strong>{summary?.employees?.inactive ?? employees.length - activeEmployees.length}</strong>
            </div>
            <div className="overview-row">
              <span>Pending leave requests</span>
              <strong>{summary?.leaves?.pending ?? pendingLeaves.length}</strong>
            </div>
            <div className="overview-row">
              <span>Approved leave today</span>
              <strong>{summary?.leaves?.approved_today ?? 0}</strong>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Attendance Snapshot</h2>
              <p>Records currently in the system</p>
            </div>
          </div>
          <div className="attendance-snapshot">
            <div className="snapshot-item">
              <span className="snapshot-dot present-dot" />
              <div><strong>{summary?.attendance?.present ?? presentCount}</strong><span>Present</span></div>
            </div>
            <div className="snapshot-item">
              <span className="snapshot-dot absent-dot" />
              <div><strong>{summary?.attendance?.absent ?? absentCount}</strong><span>Absent</span></div>
            </div>
          </div>
          <button className="btn btn-secondary full-width" onClick={() => setActivePage('Attendance')}>
            Manage Attendance →
          </button>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Quick Actions</h2>
            <p>Common workforce operations</p>
          </div>
        </div>
        <div className="quick-actions">
          <button className="quick-action" onClick={() => openEmployeeForm()}>
            <span>＋</span><strong>Add Employee</strong><small>Register a team member</small>
          </button>
          <button className="quick-action" onClick={() => openShiftForm()}>
            <span>◷</span><strong>Create Shift</strong><small>Configure shift timings</small>
          </button>
          <button className="quick-action" onClick={() => setActivePage('Staffing')}>
            <span>▤</span><strong>Staffing Plan</strong><small>Set required headcount</small>
          </button>
          <button className="quick-action" onClick={() => setActivePage('Roster')}>
            <span>▦</span><strong>Generate Roster</strong><small>Build daily assignments</small>
          </button>
          <button className="quick-action" onClick={() => { setLeaveForm(emptyLeave); setLeaveModal(true) }}>
            <span>▧</span><strong>New Leave</strong><small>Submit a leave request</small>
          </button>
          <button className="quick-action" onClick={() => setActivePage('Attendance')}>
            <span>✓</span><strong>Attendance</strong><small>Record employee attendance</small>
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Recent Employees</h2>
            <p>Latest registered team members</p>
          </div>
          <button className="btn btn-secondary" onClick={() => setActivePage('Employees')}>View all</button>
        </div>
        {employees.length === 0 ? <EmptyState>No employees added yet.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Employee</th><th>Employee ID</th><th>Brand</th><th>Process</th><th>Status</th></tr>
              </thead>
              <tbody>
                {employees.slice(0, 5).map((employee) => (
                  <tr key={employee.id}>
                    <td><strong>{employee.full_name}</strong><small className="table-subtext">{employee.email}</small></td>
                    <td>{employee.employee_id}</td>
                    <td>{employee.brand}</td>
                    <td>{employee.process}</td>
                    <td><StatusBadge value={employee.employment_status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // EMPLOYEES PAGE
  // -----------------------------------------

  const renderEmployees = () => (
    <>
      <PageHeader
        title="Employees"
        description="Manage employee profiles, departments and employment status."
        action={<button className="btn btn-primary" onClick={() => openEmployeeForm()}>＋ Add Employee</button>}
      />

      <section className="panel">
        <div className="toolbar">
          <input
            className="search-input"
            placeholder="Search name, ID, email, brand or process..."
            value={searchEmployee}
            onChange={(event) => setSearchEmployee(event.target.value)}
          />
          <span className="record-count">{filteredEmployees.length} employees</span>
        </div>

        {filteredEmployees.length === 0 ? <EmptyState>No matching employees found.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Employee</th><th>ID</th><th>Phone</th><th>Brand</th>
                  <th>Process</th><th>Joining Date</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((employee) => (
                  <tr key={employee.id}>
                    <td><strong>{employee.full_name}</strong><small className="table-subtext">{employee.email}</small></td>
                    <td>{employee.employee_id}</td>
                    <td>{employee.phone}</td>
                    <td>{employee.brand}</td>
                    <td>{employee.process}</td>
                    <td>{formatDate(employee.joining_date)}</td>
                    <td><StatusBadge value={employee.employment_status} /></td>
                    <td>
                      <div className="table-actions">
                        <button className="text-btn" onClick={() => openEmployeeForm(employee)}>Edit</button>
                        <button className="text-btn" onClick={() => toggleEmployee(employee)}>
                          {employee.employment_status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                        </button>
                        <button className="text-btn danger-text" onClick={() => deleteEmployee(employee)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // SHIFTS PAGE
  // -----------------------------------------

  const renderShifts = () => (
    <>
      <PageHeader
        title="Shift Management"
        description="Create and manage shift schedules and timings."
        action={<button className="btn btn-primary" onClick={() => openShiftForm()}>＋ Create Shift</button>}
      />

      <div className="stats-grid compact-stats">
        <StatCard label="Total Shifts" value={shifts.length} icon="◷" />
        <StatCard label="Active Shifts" value={activeShifts.length} icon="✓" />
        <StatCard label="Inactive Shifts" value={shifts.length - activeShifts.length} icon="Ⅱ" />
      </div>

      <section className="panel">
        {shifts.length === 0 ? <EmptyState>No shifts created yet.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Shift</th><th>Code</th><th>Type</th><th>Start</th><th>End</th><th>Break</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {shifts.map((shift) => (
                  <tr key={shift.id}>
                    <td><strong>{shift.shift_name}</strong></td>
                    <td>{shift.shift_code}</td>
                    <td>{shift.shift_type}</td>
                    <td>{formatTime(shift.start_time)}</td>
                    <td>{formatTime(shift.end_time)}</td>
                    <td>{shift.break_duration} min</td>
                    <td><StatusBadge value={shift.is_active ? 'ACTIVE' : 'INACTIVE'} /></td>
                    <td>
                      <div className="table-actions">
                        <button className="text-btn" onClick={() => openShiftForm(shift)}>Edit</button>
                        <button className="text-btn" onClick={() => toggleShift(shift)}>
                          {shift.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // STAFFING PAGE
  // -----------------------------------------

  const renderStaffing = () => (
    <>
      <PageHeader
        title="Staffing Requirements"
        description="Define how many employees are required for each shift and date."
      />

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Add Staffing Requirement</h2><p>Set a target headcount for a shift.</p></div>
        </div>

        <form className="form-grid" onSubmit={saveRequirement}>
          <label>Shift
            <select required value={requirementForm.shift} onChange={(e) => setRequirementForm({ ...requirementForm, shift: e.target.value })}>
              <option value="">Select shift</option>
              {activeShifts.map((shift) => <option key={shift.id} value={shift.id}>{shift.shift_name}</option>)}
            </select>
          </label>
          <label>Requirement Date
            <input type="date" required value={requirementForm.requirement_date} onChange={(e) => setRequirementForm({ ...requirementForm, requirement_date: e.target.value })} />
          </label>
          <label>Required Employees
            <input type="number" min="1" required value={requirementForm.required_employees} onChange={(e) => setRequirementForm({ ...requirementForm, required_employees: e.target.value })} />
          </label>
          <div className="form-submit"><button className="btn btn-primary" disabled={saving || !activeShifts.length}>{saving ? 'Saving...' : 'Save Requirement'}</button></div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><h2>Configured Requirements</h2><p>{requirements.length} staffing requirements</p></div></div>
        {requirements.length === 0 ? <EmptyState>No staffing requirements configured.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Shift</th><th>Required Employees</th><th>Actions</th></tr></thead>
              <tbody>
                {requirements.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.requirement_date)}</td>
                    <td>{item.shift_name || shifts.find((s) => s.id === item.shift)?.shift_name || `Shift #${item.shift}`}</td>
                    <td><strong>{item.required_employees}</strong></td>
                    <td><button className="text-btn danger-text" onClick={() => deleteRequirement(item)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // ROSTER PAGE
  // -----------------------------------------

  const renderRoster = () => (
    <>
      <PageHeader
        title="Roster Management"
        description="Generate, review and manually manage employee shift assignments."
        action={<button className="btn btn-primary" onClick={generateRoster} disabled={generating}>{generating ? 'Generating...' : '✦ Generate Roster'}</button>}
      />

      <section className="panel">
        <div className="roster-toolbar">
          <label>Select Roster Date
            <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
          </label>
          <button className="btn btn-secondary" onClick={() => openAssignmentForm()}>＋ Manual Assignment</button>
        </div>
      </section>

      {generationResult && (
        <section className="panel generation-panel">
          <div className="panel-heading">
            <div><h2>Generation Results</h2><p>{generationResult.message}</p></div>
            <StatusBadge value={generationResult.success ? 'SUCCESS' : 'SHORTAGE'} />
          </div>
          <div className="result-stats">
            <div><strong>{generationResult.generated_count ?? 0}</strong><span>New assignments</span></div>
            <div><strong>{generationResult.preserved_count ?? 0}</strong><span>Preserved assignments</span></div>
            <div><strong>{generationResult.total_assigned ?? 0}</strong><span>Total assigned</span></div>
          </div>
          {generationResult.shortages?.length > 0 && (
            <div className="alert alert-warning">
              <strong>Staffing shortages</strong>
              {generationResult.shortages.map((item, index) => (
                <p key={index}>{item.shift}: {item.assigned}/{item.required} assigned — shortage {item.shortage}</p>
              ))}
            </div>
          )}
          {generationResult.skipped?.length > 0 && (
            <details className="details-block">
              <summary>View skipped employees ({generationResult.skipped.length})</summary>
              {generationResult.skipped.map((item, index) => <p key={index}>{item.employee} — {item.shift}</p>)}
            </details>
          )}
        </section>
      )}

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Daily Roster</h2><p>{formatDate(selectedDate)} · {assignments.length} assignments</p></div>
          <button className="btn btn-secondary" onClick={() => loadAssignments(selectedDate)}>↻ Refresh</button>
        </div>

        {assignments.length === 0 ? <EmptyState>No assignments for this date. Add staffing requirements and generate the roster.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Employee</th><th>Employee ID</th><th>Brand</th><th>Process</th><th>Shift</th><th>Timing</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => (
                  <tr key={assignment.id}>
                    <td><strong>{assignment.employee_name}</strong></td>
                    <td>{assignment.employee_id}</td>
                    <td>{assignment.brand}</td>
                    <td>{assignment.process}</td>
                    <td>{assignment.shift_name}</td>
                    <td>{formatTime(assignment.start_time)} – {formatTime(assignment.end_time)}</td>
                    <td><StatusBadge value={assignment.status} /></td>
                    <td>
                      <div className="table-actions">
                        <button className="text-btn" onClick={() => openAssignmentForm(assignment)}>Edit</button>
                        <button className="text-btn danger-text" onClick={() => cancelAssignment(assignment)}>Cancel</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // LEAVE MANAGEMENT PAGE
  // -----------------------------------------

  const renderLeaves = () => (
    <>
      <PageHeader
        title="Leave Management"
        description="Review employee leave requests and manage approvals."
        action={<button className="btn btn-primary" onClick={() => { setLeaveForm(emptyLeave); setLeaveModal(true) }}>＋ New Leave Request</button>}
      />

      <div className="stats-grid compact-stats">
        <StatCard label="Total Requests" value={leaves.length} icon="▧" />
        <StatCard label="Pending" value={pendingLeaves.length} icon="◷" />
        <StatCard label="Approved" value={leaves.filter((l) => l.status === 'APPROVED').length} icon="✓" />
        <StatCard label="Rejected" value={leaves.filter((l) => l.status === 'REJECTED').length} icon="×" />
      </div>

      <section className="panel">
        <div className="panel-heading"><div><h2>Leave Requests</h2><p>Approve or reject employee requests.</p></div></div>
        {leaves.length === 0 ? <EmptyState>No leave requests submitted.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Employee</th><th>Employee ID</th><th>From</th><th>To</th><th>Reason</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {leaves.map((leave) => (
                  <tr key={leave.id}>
                    <td><strong>{leave.employee_name || `Employee #${leave.employee}`}</strong></td>
                    <td>{leave.employee_code || leave.employee}</td>
                    <td>{formatDate(leave.start_date)}</td>
                    <td>{formatDate(leave.end_date)}</td>
                    <td className="reason-cell">{leave.reason}</td>
                    <td><StatusBadge value={leave.status} /></td>
                    <td>
                      <div className="table-actions">
                        {leave.status === 'PENDING' && (
                          <>
                            <button className="text-btn success-text" onClick={() => updateLeaveStatus(leave, 'APPROVED')}>Approve</button>
                            <button className="text-btn danger-text" onClick={() => updateLeaveStatus(leave, 'REJECTED')}>Reject</button>
                          </>
                        )}
                        <button className="text-btn danger-text" onClick={() => deleteLeave(leave)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // ATTENDANCE PAGE
  // -----------------------------------------

  const renderAttendance = () => (
    <>
      <PageHeader
        title="Attendance Management"
        description="Record and review attendance for scheduled employees."
      />

      <div className="stats-grid compact-stats">
        <StatCard label="Attendance Records" value={attendance.length} icon="▤" />
        <StatCard label="Present" value={presentCount} icon="✓" />
        <StatCard label="Absent" value={absentCount} icon="×" />
        <StatCard label="Late" value={attendance.filter((a) => a.status === 'LATE').length} icon="◷" />
      </div>

      <section className="panel">
        <div className="panel-heading"><div><h2>Record Attendance</h2><p>Select a roster assignment and record its attendance.</p></div></div>
        <form className="form-grid" onSubmit={saveAttendance}>
          <label>Roster Assignment
            <select required value={attendanceForm.assignment} onChange={(e) => setAttendanceForm({ ...attendanceForm, assignment: e.target.value })}>
              <option value="">Select assignment</option>
              {assignments.map((assignment) => (
                <option key={assignment.id} value={assignment.id}>
                  {assignment.employee_name} — {assignment.shift_name} ({assignment.shift_date})
                </option>
              ))}
            </select>
          </label>
          <label>Attendance Status
            <select value={attendanceForm.status} onChange={(e) => setAttendanceForm({ ...attendanceForm, status: e.target.value })}>
              <option value="PRESENT">Present</option>
              <option value="ABSENT">Absent</option>
              <option value="LATE">Late</option>
              <option value="HALF_DAY">Half Day</option>
            </select>
          </label>
          <label>Check In
            <input type="datetime-local" value={attendanceForm.check_in} onChange={(e) => setAttendanceForm({ ...attendanceForm, check_in: e.target.value })} />
          </label>
          <label>Check Out
            <input type="datetime-local" value={attendanceForm.check_out} onChange={(e) => setAttendanceForm({ ...attendanceForm, check_out: e.target.value })} />
          </label>
          <label className="form-wide">Notes
            <textarea rows="2" value={attendanceForm.notes} onChange={(e) => setAttendanceForm({ ...attendanceForm, notes: e.target.value })} placeholder="Optional attendance notes" />
          </label>
          <div className="form-submit"><button className="btn btn-primary" disabled={saving || !assignments.length}>{saving ? 'Saving...' : 'Save Attendance'}</button></div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><h2>Attendance Records</h2><p>Recorded attendance history.</p></div></div>
        {attendance.length === 0 ? <EmptyState>No attendance records found.</EmptyState> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Employee</th><th>Employee ID</th><th>Date</th><th>Shift</th><th>Status</th><th>Check In</th><th>Check Out</th><th>Actions</th></tr></thead>
              <tbody>
                {attendance.map((item) => (
                  <tr key={item.id}>
                    <td><strong>{item.employee_name || '--'}</strong></td>
                    <td>{item.employee_code || '--'}</td>
                    <td>{formatDate(item.shift_date)}</td>
                    <td>{item.shift_name || '--'}</td>
                    <td><StatusBadge value={item.status} /></td>
                    <td>{item.check_in ? new Date(item.check_in).toLocaleString() : '--'}</td>
                    <td>{item.check_out ? new Date(item.check_out).toLocaleString() : '--'}</td>
                    <td><button className="text-btn danger-text" onClick={() => deleteAttendance(item)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )

  // -----------------------------------------
  // MODALS
  // -----------------------------------------

  const renderEmployeeModal = () => employeeModal && (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setEmployeeModal(false) }}>
      <div className="modal">
        <div className="modal-header">
          <div><h2>{editingEmployee ? 'Edit Employee' : 'Add Employee'}</h2><p>Enter employee details below.</p></div>
          <button className="modal-close" onClick={() => setEmployeeModal(false)}>×</button>
        </div>
        <form onSubmit={saveEmployee}>
          <div className="form-grid">
            <label>Employee ID<input required value={employeeForm.employee_id} onChange={(e) => setEmployeeForm({ ...employeeForm, employee_id: e.target.value })} /></label>
            <label>Full Name<input required value={employeeForm.full_name} onChange={(e) => setEmployeeForm({ ...employeeForm, full_name: e.target.value })} /></label>
            <label>Email<input type="email" required value={employeeForm.email} onChange={(e) => setEmployeeForm({ ...employeeForm, email: e.target.value })} /></label>
            <label>Phone<input required value={employeeForm.phone} onChange={(e) => setEmployeeForm({ ...employeeForm, phone: e.target.value })} /></label>
            <label>Brand<input required value={employeeForm.brand} onChange={(e) => setEmployeeForm({ ...employeeForm, brand: e.target.value })} /></label>
            <label>Process<input required value={employeeForm.process} onChange={(e) => setEmployeeForm({ ...employeeForm, process: e.target.value })} /></label>
            <label>Joining Date<input type="date" required value={employeeForm.joining_date} onChange={(e) => setEmployeeForm({ ...employeeForm, joining_date: e.target.value })} /></label>
            <label>Employment Status
              <select value={employeeForm.employment_status} onChange={(e) => setEmployeeForm({ ...employeeForm, employment_status: e.target.value })}>
                <option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option>
              </select>
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setEmployeeModal(false)}>Cancel</button>
            <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Employee'}</button>
          </div>
        </form>
      </div>
    </div>
  )

  const renderShiftModal = () => shiftModal && (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setShiftModal(false) }}>
      <div className="modal">
        <div className="modal-header">
          <div><h2>{editingShift ? 'Edit Shift' : 'Create Shift'}</h2><p>Configure shift details and timings.</p></div>
          <button className="modal-close" onClick={() => setShiftModal(false)}>×</button>
        </div>
        <form onSubmit={saveShift}>
          <div className="form-grid">
            <label>Shift Name<input required value={shiftForm.shift_name} onChange={(e) => setShiftForm({ ...shiftForm, shift_name: e.target.value })} /></label>
            <label>Shift Code<input required value={shiftForm.shift_code} onChange={(e) => setShiftForm({ ...shiftForm, shift_code: e.target.value.toUpperCase() })} /></label>
            <label>Shift Type
              <select value={shiftForm.shift_type} onChange={(e) => setShiftForm({ ...shiftForm, shift_type: e.target.value })}>
                <option value="MORNING">Morning</option><option value="AFTERNOON">Afternoon</option><option value="NIGHT">Night</option><option value="GENERAL">General</option>
              </select>
            </label>
            <label>Break Duration (minutes)<input type="number" min="0" value={shiftForm.break_duration} onChange={(e) => setShiftForm({ ...shiftForm, break_duration: Number(e.target.value) })} /></label>
            <label>Start Time<input type="time" required value={shiftForm.start_time} onChange={(e) => setShiftForm({ ...shiftForm, start_time: e.target.value })} /></label>
            <label>End Time<input type="time" required value={shiftForm.end_time} onChange={(e) => setShiftForm({ ...shiftForm, end_time: e.target.value })} /></label>
            <label className="checkbox-label"><input type="checkbox" checked={shiftForm.is_active} onChange={(e) => setShiftForm({ ...shiftForm, is_active: e.target.checked })} /> Active shift</label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setShiftModal(false)}>Cancel</button>
            <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Shift'}</button>
          </div>
        </form>
      </div>
    </div>
  )

  const renderLeaveModal = () => leaveModal && (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setLeaveModal(false) }}>
      <div className="modal">
        <div className="modal-header">
          <div><h2>New Leave Request</h2><p>Submit leave for an employee.</p></div>
          <button className="modal-close" onClick={() => setLeaveModal(false)}>×</button>
        </div>
        <form onSubmit={saveLeave}>
          <div className="form-grid">
            <label className="form-wide">Employee
              <select required value={leaveForm.employee} onChange={(e) => setLeaveForm({ ...leaveForm, employee: e.target.value })}>
                <option value="">Select employee</option>
                {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.employee_id} — {employee.full_name}</option>)}
              </select>
            </label>
            <label>Start Date<input type="date" required value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} /></label>
            <label>End Date<input type="date" required value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} /></label>
            <label className="form-wide">Reason<textarea required rows="3" value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} placeholder="Enter reason for leave" /></label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setLeaveModal(false)}>Cancel</button>
            <button className="btn btn-primary" disabled={saving || !employees.length}>{saving ? 'Submitting...' : 'Submit Request'}</button>
          </div>
        </form>
      </div>
    </div>
  )

  const renderAssignmentModal = () => assignmentModal && (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setAssignmentModal(false) }}>
      <div className="modal">
        <div className="modal-header">
          <div><h2>{editingAssignment ? 'Edit Assignment' : 'Manual Assignment'}</h2><p>Roster date: {formatDate(selectedDate)}</p></div>
          <button className="modal-close" onClick={() => setAssignmentModal(false)}>×</button>
        </div>
        <form onSubmit={saveAssignment}>
          <div className="form-grid">
            <label className="form-wide">Employee
              <select name="employee" required defaultValue={editingAssignment?.employee_id ? employees.find((e) => e.employee_id === editingAssignment.employee_id)?.id || '' : ''}>
                <option value="">Select employee</option>
                {activeEmployees.map((employee) => <option key={employee.id} value={employee.id}>{employee.employee_id} — {employee.full_name}</option>)}
              </select>
            </label>
            <label className="form-wide">Shift
              <select name="shift" required defaultValue={editingAssignment?.shift_id || ''}>
                <option value="">Select shift</option>
                {activeShifts.map((shift) => <option key={shift.id} value={shift.id}>{shift.shift_name}</option>)}
              </select>
            </label>
            <label>Status
              <select name="status" defaultValue={editingAssignment?.status || 'SCHEDULED'}>
                <option value="SCHEDULED">Scheduled</option><option value="COMPLETED">Completed</option>
              </select>
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setAssignmentModal(false)}>Cancel</button>
            <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Assignment'}</button>
          </div>
        </form>
      </div>
    </div>
  )

  // -----------------------------------------
  // PAGE ROUTER
  // -----------------------------------------

  const pageContent = {
    Dashboard: renderDashboard,
    Employees: renderEmployees,
    Shifts: renderShifts,
    Staffing: renderStaffing,
    Roster: renderRoster,
    'Leave Management': renderLeaves,
    Attendance: renderAttendance,
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">DS</div>
          <div><strong>DataStraw</strong><span>SMART ROSTER</span></div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        {['OVERVIEW', 'WORKFORCE', 'SCHEDULING'].map((section) => (
          <div className="nav-section" key={section}>
            <div className="nav-section-label">{section}</div>
            {navigation.filter((item) => item.section === section).map((item) => (
              <button
                key={item.name}
                className={`nav-item ${activePage === item.name ? 'active' : ''}`}
                onClick={() => setActivePage(item.name)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.name}</span>
                {item.name === 'Leave Management' && pendingLeaves.length > 0 && (
                  <span className="nav-count">{pendingLeaves.length}</span>
                )}
              </button>
            ))}
          </div>
        ))}

        <div className="sidebar-bottom">
          <div className="system-status"><span /> API connection configured</div>
          <small>DataStraw Smart Roster</small>
          <small>Workforce Management</small>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace</span>
            <strong>{activePage}</strong>
          </div>
          <div className="topbar-right">
            <span className="today-label">{formatDate(today())}</span>
            <button className="profile-avatar" title="Administrator">A</button>
          </div>
        </header>

        <div className="content-area">
  {pageNotices[activePage] && (
    <div
      className={`toast ${
        pageNotices[activePage].type === 'error'
          ? 'toast-error'
          : 'toast-success'
      }`}
      role="alert"
    >
      <span>
        {pageNotices[activePage].type === 'error' ? '⚠' : '✓'}
      </span>
      {pageNotices[activePage].text}
      <button
        className="notice-close"
        onClick={() =>
          setPageNotices((previous) => {
            const updated = { ...previous }
            delete updated[activePage]
            return updated
          })
        }
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  )}

          {loading ? (
            <div className="loading-state"><div className="loader" />Loading workspace data...</div>
          ) : (
            (pageContent[activePage] || renderDashboard)()
          )}
        </div>
      </main>

      {renderEmployeeModal()}
      {renderShiftModal()}
      {renderLeaveModal()}
      {renderAssignmentModal()}
    </div>
  )
}
