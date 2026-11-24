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

const emptyBrand = { name: '', code: '', description: '', is_active: true }
const emptyProcess = { name: '', code: '', description: '', is_active: true }

function BrandsAndProcesses() {
  const [brands, setBrands] = useState([])
  const [processes, setProcesses] = useState([])
  const [brandForm, setBrandForm] = useState(emptyBrand)
  const [processForm, setProcessForm] = useState(emptyProcess)
  const [editingBrand, setEditingBrand] = useState(null)
  const [editingProcess, setEditingProcess] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    const [brandData, processData] = await Promise.all([
      request('/brands/'),
      request('/processes/'),
    ])
    setBrands(listOf(brandData))
    setProcesses(listOf(processData))
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

  const saveBrand = (event) => {
    event.preventDefault()
    run(
      () => request(
        editingBrand ? `/brands/${editingBrand.id}/` : '/brands/',
        {
          method: editingBrand ? 'PUT' : 'POST',
          body: JSON.stringify(brandForm),
        }
      ).then(() => {
        setBrandForm(emptyBrand)
        setEditingBrand(null)
      }),
      editingBrand ? 'Brand updated.' : 'Brand added.'
    )
  }

  const saveProcess = (event) => {
    event.preventDefault()
    run(
      () => request(
        editingProcess ? `/processes/${editingProcess.id}/` : '/processes/',
        {
          method: editingProcess ? 'PUT' : 'POST',
          body: JSON.stringify(processForm),
        }
      ).then(() => {
        setProcessForm(emptyProcess)
        setEditingProcess(null)
      }),
      editingProcess ? 'Process updated.' : 'Process added.'
    )
  }

  const toggle = (path, item, label) => run(
    () => request(`${path}${item.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !item.is_active }),
    }),
    `${label} ${item.is_active ? 'deactivated' : 'activated'}.`
  )

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Brands and Processes</h1>
          <p>Add, edit, or deactivate the brands and processes the roster uses.</p>
        </div>
      </div>

    {message && <div className="toast toast-success" role="alert"><span>✓</span>{message}</div>}
    {error && <div className="toast toast-error" role="alert"><span>⚠</span>{error}</div>}
      <section className="panel">
        <div className="panel-heading">
          <div><h2>Brands</h2><p>{brands.length} brands</p></div>
        </div>

        <form className="form-grid" onSubmit={saveBrand}>
          <label>Name
            <input required value={brandForm.name} onChange={(e) => setBrandForm({ ...brandForm, name: e.target.value })} />
          </label>
          <label>Code
            <input required value={brandForm.code} onChange={(e) => setBrandForm({ ...brandForm, code: e.target.value.toUpperCase() })} />
          </label>
          <label className="form-wide">Description
            <input value={brandForm.description} onChange={(e) => setBrandForm({ ...brandForm, description: e.target.value })} />
          </label>
          <div className="form-submit">
            <button className="btn btn-primary">{editingBrand ? 'Save Brand' : 'Add Brand'}</button>
            {editingBrand && (
              <button type="button" className="btn btn-secondary" onClick={() => { setEditingBrand(null); setBrandForm(emptyBrand) }}>
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Name</th><th>Code</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {brands.map((brand) => (
                <tr key={brand.id}>
                  <td><strong>{brand.name}</strong></td>
                  <td>{brand.code}</td>
                  <td>{brand.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <div className="table-actions">
                      <button className="text-btn" onClick={() => { setEditingBrand(brand); setBrandForm({ name: brand.name, code: brand.code, description: brand.description || '', is_active: brand.is_active }) }}>Edit</button>
                      <button className="text-btn" onClick={() => toggle('/brands/', brand, 'Brand')}>
                        {brand.is_active ? 'Deactivate' : 'Activate'}
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
          <div><h2>Processes</h2><p>{processes.length} processes</p></div>
        </div>

        <form className="form-grid" onSubmit={saveProcess}>
          <label>Name
            <input required value={processForm.name} onChange={(e) => setProcessForm({ ...processForm, name: e.target.value })} />
          </label>
          <label>Code
            <input required value={processForm.code} onChange={(e) => setProcessForm({ ...processForm, code: e.target.value.toUpperCase() })} />
          </label>
          <label className="form-wide">Description
            <input value={processForm.description} onChange={(e) => setProcessForm({ ...processForm, description: e.target.value })} />
          </label>
          <div className="form-submit">
            <button className="btn btn-primary">{editingProcess ? 'Save Process' : 'Add Process'}</button>
            {editingProcess && (
              <button type="button" className="btn btn-secondary" onClick={() => { setEditingProcess(null); setProcessForm(emptyProcess) }}>
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Name</th><th>Code</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {processes.map((process) => (
                <tr key={process.id}>
                  <td><strong>{process.name}</strong></td>
                  <td>{process.code}</td>
                  <td>{process.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <div className="table-actions">
                      <button className="text-btn" onClick={() => { setEditingProcess(process); setProcessForm({ name: process.name, code: process.code, description: process.description || '', is_active: process.is_active }) }}>Edit</button>
                      <button className="text-btn" onClick={() => toggle('/processes/', process, 'Process')}>
                        {process.is_active ? 'Deactivate' : 'Activate'}
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

export default BrandsAndProcesses