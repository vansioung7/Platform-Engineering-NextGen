package main

deny[msg] {
  rc := input.resource_changes[_]
  rc.change.after.tags
  not rc.change.after.tags.owner
  msg := sprintf("resource %s is missing required tag: owner", [rc.address])
}

deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_security_group"
  rc.change.after.ingress
  ingress := rc.change.after.ingress[_]
  ingress.cidr_blocks
  ingress.cidr_blocks[_] == "0.0.0.0/0"
  ingress.from_port <= 22
  ingress.to_port >= 22
  msg := sprintf("resource %s exposes SSH to 0.0.0.0/0", [rc.address])
}
