import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig, loadEnv } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const projectRoot = path.dirname(fileURLToPath(import.meta.url))

function readEnvFile(root) {
	const envPath = path.join(root, '.env')
	const env = {}
	if (!fs.existsSync(envPath)) {
		return env
	}
	for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
		const trimmed = line.trim()
		if (trimmed.length == 0 || trimmed.startsWith('#')) {
			continue
		}
		const index = trimmed.indexOf('=')
		if (index < 0) {
			continue
		}
		env[trimmed.slice(0, index).trim()] = trimmed.slice(index + 1).trim()
	}
	return env
}

function getHermesTarget(env) {
	const host = env.VITE_HERMES_HOST || '127.0.0.1'
	const port = env.VITE_HERMES_PORT || '8642'
	return `http://${host}:${port}`
}

function getBizTarget(env) {
	const host = env.VITE_HERMES_HOST || '127.0.0.1'
	const port = env.VITE_BIZ_API_PORT || '8181'
	return `http://${host}:${port}`
}

function devProxy(name, prefix, target) {
	return {
		name: name,
		configureServer(server) {
			server.middlewares.use((req, res, next) => {
				if (req.url == null || !req.url.startsWith(prefix)) {
					next()
					return
				}

				if (req.method === 'OPTIONS') {
					res.statusCode = 204
					res.end()
					return
				}

				const targetPath = req.url.replace(new RegExp('^' + prefix), '') || '/'
				const targetUrl = target + targetPath

				const forwardRequest = (body) => {
					const headers = {}
					const auth = req.headers['authorization']
					const contentType = req.headers['content-type']
					if (auth != null) {
						headers['Authorization'] = auth
					}
					if (contentType != null) {
						headers['Content-Type'] = contentType
					}

					fetch(targetUrl, {
						method: req.method,
						headers,
						body: req.method !== 'GET' && req.method !== 'HEAD' ? body : undefined
					}).then(async (response) => {
						res.statusCode = response.status
						const contentTypeHeader = response.headers.get('content-type')
						if (contentTypeHeader != null) {
							res.setHeader('Content-Type', contentTypeHeader)
						}
						res.end(await response.text())
					}).catch((err) => {
						res.statusCode = 502
						res.setHeader('Content-Type', 'application/json')
						res.end(JSON.stringify({ error: String(err), target: targetUrl }))
					})
				}

				if (req.method === 'GET' || req.method === 'HEAD') {
					forwardRequest(undefined)
					return
				}

				const chunks = []

				req.on('data', (chunk) => {
					chunks.push(chunk)
				})
				req.on('end', () => {
					const body = chunks.length > 0 ? Buffer.concat(chunks) : undefined
					forwardRequest(body)
				})
			})
		}
	}
}

export default defineConfig(({ mode }) => {
	const env = Object.assign(readEnvFile(projectRoot), loadEnv(mode, projectRoot, ''))
	const hermesTarget = getHermesTarget(env)
	const bizTarget = getBizTarget(env)
	console.log('[hermes-dev-proxy] target:', hermesTarget)
	console.log('[biz-dev-proxy] target:', bizTarget)

	return {
		plugins: [
			uni(),
			devProxy('hermes-dev-proxy', '/hermes-api', hermesTarget),
			devProxy('biz-dev-proxy', '/biz-api', bizTarget)
		]
	}
})
