# Test the Sand3D harness

From AgentDock, build against the pinned upstream checkout and run the installed
console entry point through its image.

```sh
image_id=$(bash /path/to/agentdock-builder/fixtures/sand3d/build.sh /path/to/sand3d sand3d-build-receipt.json)
docker run --rm --network none "$image_id" --help
bash /path/to/agentdock-builder/fixtures/sand3d/run.sh "$image_id" sand3d-build-receipt.json /path/to/new-evidence-directory
python3 -B -m unittest discover -s tests -p test_verify_sand3d_glb.py
```

The fixture exports a default bracket and passes the GLB to the independent
verifier. The verifier's CLI tests also exercise scaled geometry, false
dimensions in the JSON metadata, a plate without the expected holes and a
truncated GLB.
