// Builds the Control, Core and MLS images in one command, in the right order.
// Core takes its ROS transport overlay straight from the Control build of
// the same run, so there is no control image tag to keep in sync by hand.
//
// Run from the repository root (the checkout directory must be named `mios`):
//   docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=..          # all images
//   TAG=ablatest docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=..
//   docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=.. --push   # build + push
//   docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=.. core     # core (+ the control build it needs)
// `--allow=fs.read=..` is required because the build context is the parent
// directory of the checkout.

variable "REPO" {
  default = "janine86"
}

variable "TAG" {
  default = "latest"
}

// Optional second tag for every image, for example a commit hash in CI.
variable "EXTRA_TAG" {
  default = ""
}

function "tags" {
  params = [name]
  result = compact([
    "${REPO}/${name}:${TAG}",
    EXTRA_TAG != "" ? "${REPO}/${name}:${EXTRA_TAG}" : "",
  ])
}

group "default" {
  targets = ["control", "core", "mls"]
}

target "control" {
  context    = ".."
  dockerfile = "mios/docker/control/Dockerfile"
  tags       = tags("ros2-control")
}

target "core" {
  context    = ".."
  dockerfile = "mios/docker/core/Dockerfile"
  tags       = tags("ros2-core")
  // `FROM ${MIOS_CONTROL_IMAGE}` in the Core Dockerfile resolves to the
  // Control target built above instead of an image pulled from a registry.
  contexts = {
    control-image = "target:control"
  }
  args = {
    MIOS_CONTROL_IMAGE = "control-image"
  }
}

// The learning service is independent of the other two; its build context is
// the repository root.
target "mls" {
  context    = "."
  dockerfile = "docker/ml_service/Dockerfile"
  tags       = tags("mls")
}
