# Express js app for the eliza client
## Features
* create/delete characters
* run character
* save character to mongo
* reply to tweets (when mentioned or when someone comments to character's twitter handle)


# Express.js App for the Eliza Client

## Features
- Create and delete characters
- Run a character
- Save characters to MongoDB
- Reply to tweets (when mentioned or when someone comments on the character's Twitter handle)

## To-Do
- [ ] post new tweets
- [ ] Build a React-based frontend

---

## Installation

### 1. Clone the Eliza repository
```sh
git clone https://github.com/elizaOS/eliza.git
```

### 2. Install dependencies
```sh
cd eliza
pnpm install
```
If the above command fails, try:
```sh
pnpm install --no-frozen-lockfile
```

### 3. Place the Express.js app file
Ensure `express_app.js` is located in the `eliza/` folder.

### 4. Build local libraries
```sh
pnpm build
```

### 5. Configure the environment
Create a `.env` file or export the following environment variables:
```sh
ATOMASDK_BEARER_AUTH=<your-atoma-bearer>
TWITTER_USERNAME=<account-username>
TWITTER_PASSWORD=<account-password>
TWITTER_EMAIL=<account-email>
```

### 6. Run the Express.js app
```sh
node express_app.js
```

---

## API Endpoints

### 1. Create a New Character
**Endpoint:** `POST http://localhost:5000/api/characters`

#### Example Request:
```sh
curl -X POST http://localhost:5000/api/characters \
-H "Content-Type: application/json" \
-d '{
  "_id": "67a4be79df95c5017529210a",
  "name": "doby_new",
  "clients": ["twitter", "direct"],
  "modelProvider": "atoma",
  "settings": {
    "voice": { "model": "en_US-male-medium" }
  },
  "bio": [
    "Dobby is a free assistant who chooses to help because of his enormous heart.",
    "Extremely devoted and will go to any length to help his friends."
  ]
}'
```

---

### 1.5 Delete a Character
**Endpoint:** `DELETE http://localhost:5000/api/characters/:name`

#### Example Request:
```sh
curl -X DELETE http://localhost:5000/api/characters/doby_new
```

---

### 2. Get Existing Characters
**Endpoint:** `GET http://localhost:5000/api/characters`

#### Example Request:
```sh
curl "http://localhost:5000/api/characters?name=doby_new"
```

#### Search by Name and Client:
```sh
curl "http://localhost:5000/api/characters?name=doby_new&client=twitter"
```

---

### 3. Run Multiple Characters
**Endpoint:** `POST http://localhost:5000/api/characters/run`

#### Example Request:
```sh
curl -X POST http://localhost:5000/api/characters/run \
-H "Content-Type: application/json" \
-d '{"characters": ["doby_new"]}'
```

---

### Notes:
- Ensure MongoDB is running before executing character-related requests.
- The Express app should be restarted if configuration changes are made.
- Logs are stored in the `logs/` directory for debugging.

---

Happy coding!