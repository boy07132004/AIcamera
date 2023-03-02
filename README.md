# AICamera

## Required

- **Make sure your camera source /dev/video0 is available.**

## How to use

Build and start containers.

```bash
docker-compose up --build
```

## API

- API docs: **http://[your_ip_address]:5000/apidocs**
- Person detection stream: **http://[your_ip_address]:5555/stream.mjpg**
- Count stay time area setting: **http://[your_ip_address]:5000/person_box_setting**