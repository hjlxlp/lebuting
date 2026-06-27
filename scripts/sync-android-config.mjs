import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..')
const envPath = path.join(root, '.env')
const outPath = path.join(root, 'nativeResources/android/res/xml/network_security_config.xml')

function readEnv(filePath) {
	if (!fs.existsSync(filePath)) {
		console.error('未找到 .env，请先复制 .env.example 为 .env')
		process.exit(1)
	}
	const env = {}
	for (const line of fs.readFileSync(filePath, 'utf8').split('\n')) {
		const trimmed = line.trim()
		if (trimmed.length == 0 || trimmed.startsWith('#')) continue
		const index = trimmed.indexOf('=')
		if (index < 0) continue
		env[trimmed.slice(0, index).trim()] = trimmed.slice(index + 1).trim()
	}
	return env
}

const env = readEnv(envPath)
const hermesHost = env.VITE_HERMES_HOST
const bizHost = env.VITE_BIZ_API_HOST || hermesHost

if (hermesHost == null || hermesHost.length == 0 || hermesHost == 'YOUR_HERMES_HOST') {
	console.error('.env 中 VITE_HERMES_HOST 未配置')
	process.exit(1)
}

const domains = new Set(['localhost', '10.0.2.2', '127.0.0.1'])
if (hermesHost.length > 0) domains.add(hermesHost)
if (bizHost.length > 0 && bizHost != '127.0.0.1' && bizHost != 'localhost') {
	domains.add(bizHost)
}

const domainLines = [...domains].map((d) => `\t\t<domain includeSubdomains="true">${d}</domain>`).join('\n')

const xml = `<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
\t<domain-config cleartextTrafficPermitted="true">
${domainLines}
\t</domain-config>
</network-security-config>
`

fs.mkdirSync(path.dirname(outPath), { recursive: true })
fs.writeFileSync(outPath, xml, 'utf8')
console.log('已生成 network_security_config.xml')
console.log('  Hermes HOST=' + hermesHost)
console.log('  Biz API HOST=' + bizHost)
