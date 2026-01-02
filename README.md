# AI Agent Platform
A platform that enables users to create, manage, and interact with AI agents via text and voice.

---

## Video Demo

Watch now at https://youtu.be/PuX-5r-xIhY

---

## Tech Stacks
- Backend: Python, FastAPI, Pytest, SQLite
- AI: OpenAI Agents SDK, Elevenlabs SDK for Text-to-Speech and Speech-to-Text
- Containerization: Docker, Docker Compose

---

## Local Developement Setup

### Get environment variables

Create a `.env` file in the project root containing your [OpenAI](https://platform.openai.com/docs/quickstart) and [Elevenlabs](https://elevenlabs.io/docs/developers/quickstart) credentials

```env
BASE_URL=https://api.openai.com/v1
API_KEY=<your-openai-api-key>
MODEL_NAME=<openai-model-id>
ELEVENLABS_API_KEY=<elevenlabs-api-key>
```

### Build and start the container:
``` shell
docker compose up -d --build
```
* The FastAPI app will be accessible at http://127.0.0.1:8000
* Swagger/OpenAPI API documentation: http://127.0.0.1:8000/docs
* ReDoc API documentation: http://127.0.0.1:8000/redoc
* Postman Collection: https://www.postman.com/maelghrib/personal-projects/collection/34947427-339968ac-d5ca-4b5f-8a1a-45edca03a6c4

### Run Tests:

```shell
docker exec -it ai-agent-platform /bin/bash -c "pytest"
 ```

---