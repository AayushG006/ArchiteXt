export async function analyzeRepository(repoUrl) {
  const response = await fetch('/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ repo_url: repoUrl })
  })

  const text = await response.text()
  let data

  try {
    data = JSON.parse(text)
  } catch (error) {
    throw new Error('Backend returned invalid JSON.')
  }

  if (!response.ok) {
    throw new Error(data.detail || 'Analysis failed.')
  }

  return data
}
