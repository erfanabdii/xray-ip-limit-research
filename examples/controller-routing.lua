-- Fragment of the recorded fixture routing script with synthetic constants.
-- A disposable fixture must generate its own nonce and configure the matching
-- local DNS server, blackhole-first outbound and loopback-only target route.
local scope = {
  ["fixture-alice@example.invalid"] = "u0",
  ["fixture-bob@example.invalid"] = "u1"
}
local ns = require("xray.dns").Servers[1]

function HandleRoute(ctx, inboundTag, sourcePort, targetPort, localPort,
 targetDomain, network, protocol, user)
 if inboundTag == "fixture-dns" then return "fixture-loopback-only" end
 local account = scope[user]
 if not account then return "fixture-loopback-only" end
 local sources = ctx:GetSourceIPs()
 if #sources ~= 1 then return "fixture-block" end
 local ip = sources[1]:String()
 if ip ~= "198.51.100.10" and ip ~= "198.51.100.11" and ip ~= "198.51.100.12" then
   return "fixture-block" end
 local name = account .. ".p" .. string.gsub(ip, "%.", "-") .. ".00000000000000000000000000000000.fixture.invalid"
 local ips, ttl, err = ns:Query(name, true, false, false)
 if err == nil and #ips == 1 and ips[1]:String() == "127.0.0.1" then
   return "fixture-loopback-only"
 end
 return "fixture-block"
end
