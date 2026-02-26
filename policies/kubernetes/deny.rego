package main

deny[msg] {
  input.kind == "Deployment"
  c := input.spec.template.spec.containers[_]
  endswith(lower(c.image), ":latest")
  msg := sprintf("deployment %s container %s uses mutable image tag ':latest'", [input.metadata.name, c.name])
}

deny[msg] {
  input.kind == "Deployment"
  c := input.spec.template.spec.containers[_]
  c.securityContext.privileged == true
  msg := sprintf("deployment %s container %s runs privileged", [input.metadata.name, c.name])
}

