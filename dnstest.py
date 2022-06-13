import dns.resolver
domain='operator-api.ocean-operator.svc.cluster.local'
srvInfo = {}
srv_records=dns.resolver.resolve(domain, 'SRV')
for srv in srv_records:
	srvInfo['weight']   = srv.weight
	srvInfo['host']     = str(srv.target).rstrip('.')
	srvInfo['priority'] = srv.priority
	srvInfo['port']     = srv.port

print(srvInfo)
