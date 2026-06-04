from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = ROOT / "stage7_deployment" / "docker" / "sui" / "Dockerfile"


class DockerImageContractTests(unittest.TestCase):
    def test_sui_image_builds_and_installs_sui_node(self):
        text = DOCKERFILE.read_text(encoding="utf-8")

        self.assertIn("--bin sui-node", text)
        self.assertIn("target/release/sui-node", text)
        self.assertIn("/usr/local/bin/sui-node", text)

    def test_sui_image_is_legacy_builder_compatible(self):
        text = DOCKERFILE.read_text(encoding="utf-8")

        self.assertNotIn("--mount=type=cache", text)
        self.assertIn("RUN cargo build --locked --release --bin sui -j 2", text)
        self.assertIn("RUN cargo build --locked --release --bin sui-node -j 2", text)
        self.assertIn("/out/sui-node", text)


if __name__ == "__main__":
    unittest.main()
