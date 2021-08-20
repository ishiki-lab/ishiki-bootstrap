docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -v /:/host \
  -v portainer_agent_data:/data \
  --restart always \
  -e EDGE=1 \
  -e EDGE_ID=569e8c38-060f-464f-93c1-cde82cc38c2f \
  -e EDGE_KEY=aHR0cHM6Ly9nYXRld2F5cy5ib3MuYXJ1cGlvdC5jb218Z2F0ZXdheXMuYm9zLmFydXBpb3QuY29tOjgwMDB8Nzk6NGM6ZDU6ZGM6MmQ6MDM6MjQ6NWE6MDE6Y2U6MDc6MTE6OGI6OTg6Y2U6ODd8MTA \
  -e CAP_HOST_MANAGEMENT=1 \
  --name portainer_edge_agent_test1 \
  portainer/agent


