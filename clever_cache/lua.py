# -*- coding: utf-8 -*-

LUA_CACHE_OBJECT = """
local obj = ARGV[1]
local timeout = ARGV[2]
local obj_key = KEYS[1]

if timeout then
    timeout = tonumber(timeout)
    redis.call('SET', obj_key, obj, 'EX', timeout)
else
    redis.call('SET', obj_key, obj)
end

for i = 2, #KEYS do
    local dependency_key = KEYS[i]

    local previous_ttl = redis.call('TTL', dependency_key)
    redis.call('SADD', dependency_key, obj_key)

    if timeout then
        if previous_ttl == -2 or (0 < previous_ttl and previous_ttl < timeout) then
            redis.call('EXPIRE', dependency_key, timeout)
        end
    else
        if previous_ttl > 0 then
            redis.call('PERSIST', dependency_key)
        end
    end
end
"""

LUA_INVALIDATE_DEPENDENTS = """
local keys_to_delete = redis.call('SUNION', unpack(KEYS))
if #keys_to_delete ~= 0 then
    redis.call('DEL', unpack(keys_to_delete))
end
redis.call('DEL', unpack(KEYS))
return keys_to_delete
"""

LUA_COLLECT_GARBAGE = """
for i, dependency_key in ipairs(redis.call('KEYS', 'clever_cache_deps:*')) do
    for j, dependent_key in ipairs(redis.call('SMEMBERS', dependency_key)) do
        local key_exists = redis.call('EXISTS', dependent_key)
        if key_exists == 0 then
            redis.call('SREM', dependency_key, dependent_key)
        end
    end
end
"""
