# AI Agent Platform
A platform that enables users to create, manage, and interact with AI agents via text and voice.

---

## Local Developement Setup

### Get environment variables

Create a `.env` file in the project root containing your OpenAI credentials

```env
BASE_URL=https://api.openai.com/v1
API_KEY=<your-openai-api-key>
MODEL_NAME=<openai-model-id>
```

### Build and start the container:
``` shell
docker compose up -d --build
```
* The FastAPI app will be accessible at `http://127.0.0.1:8000`
* Swagger/OpenAPI API documentation: `http://127.0.0.1:8000/docs`
* ReDoc API documentation: `http://127.0.0.1:8000/redoc`
* Postman Collection: `https://www.postman.com/maelghrib/personal-projects/collection/34947427-339968ac-d5ca-4b5f-8a1a-45edca03a6c4`

### Run Tests:

```shell
docker exec -it ai-agent-platform /bin/bash -c "pytest"
 ```

---