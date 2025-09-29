from petlib.ec import EcGroup

# Using the petlib library group operations to generate group and group values
group = EcGroup()
g = group.generator()
order = group.order()

# Generating secret key at random from the EC group
sk = order.random()
pk = sk * g

print(f"g: {g}")
print(f"order: {order}")
print(f"secret key: {sk}")
print(f"public key: {pk}")