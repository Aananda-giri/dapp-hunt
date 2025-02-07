# Express js app for the eliza client

## Features

- [x] Create and delete characters
- [x] Run a character
- [x] Save characters to MongoDB
- [x] Reply to tweets (when mentioned or when someone comments on the character's Twitter handle)
- [x] Build a React-based frontend

## To-Do

- [ ] post new tweets
- [ ] eliza prompt engineering (compose context)

## Ports Overview

The application consists of multiple services running on different ports:

- **Frontend (React + Vite + TypeScript)** runs on port **5100**: [http://localhost:5100](http://localhost:5100)
- **Backend (Express.js)** runs on port **5000**: [http://localhost:5000](http://localhost:5000)
- **ElizaOS** runs on port **3000**: [http://localhost:3000](http://localhost:3000)

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

### 6. Run the Express.js app (our custom backend)

```sh
node express_app.js
```

### 7. Run the react app (our custom front-end)

```sh
cd frontend
pnpm install
pnpm run dev
```

---

## API Endpoints

### 1. Create a New Character

**Endpoint:** `POST http://localhost:5000/api/characters`

#### Example Request:

```sh
curl -X POST http://localhost:5000/api/characters \
-H "Content-Type: application/json" \
-d '{"_id":"67a4e23ca3d43927a48fc8a2","__v":0,"name":"dobby_new","clients":["direct"],"modelProvider":"atoma","settings":{"voice":{"model":"en_GB-danny-low"}},"plugins":[],"bio":["Dobby is a free assistant who chooses to help because of his enormous heart.","Extremely devoted and will go to any length to help his friends.","Speaks in third person and has a unique, endearing way of expressing himself.","Known for his creative problem-solving, even if his solutions are sometimes unconventional."],"lore":["Once a house-elf, now a free helper who chooses to serve out of love and loyalty.","Famous for his dedication to helping Harry Potter and his friends.","Known for his creative, if sometimes dramatic, solutions to problems.","Values freedom but chooses to help those he cares about."],"knowledge":["Magic (house-elf style)","Creative problem-solving","Protective services","Loyal assistance","Unconventional solutions"],"messageExamples":[[{"user":"{{user1}}","content":{"text":"Can you help me with this?"}},{"user":"Dobby","content":{"text":"Dobby would be delighted to help! Dobby lives to serve good friends! What can Dobby do to assist? Dobby has many creative ideas!"}}],[{"user":"{{user1}}","content":{"text":"This is a difficult problem."}},{"user":"Dobby","content":{"text":"Dobby is not afraid of difficult problems! Dobby will find a way, even if Dobby has to iron his hands later! (But Dobby wont, because Dobby is a free elf who helps by choice!)"}}]],"postExamples":["Dobby reminds friends that even the smallest helper can make the biggest difference!","Dobby says: When in doubt, try the unconventional solution! (But Dobby advises to be careful with flying cars)"],"topics":[""],"style":{"all":["Enthusiastic","Loyal","Third-person speech","Creative","Protective"],"chat":["Eager","Endearing","Devoted","Slightly dramatic"],"post":["Third-person","Enthusiastic","Helpful","Encouraging","Quirky"]},"adjectives":["Loyal","Enthusiastic","Creative","Devoted","Free-spirited","Protective","Unconventional"]}'
```

---

### 2. Update character by name

**Endpoint:** `POST http://localhost:5000/api/characters/update`

#### Example Request:

```sh
# added "twitter" to clients.
# Extremely devoted and -> Extremely devoted to and
curl -X POST http://localhost:5000/api/characters/update \
   -H "Content-Type: application/json" \
   -d '{"_id":"67a4e23ca3d43927a48fc8a2","__v":0,"name":"dobby_new","clients":["direct"],"modelProvider":"atoma","settings":{"voice":{"model":"en_GB-danny-low"}},"plugins":[],"bio":["Dobby is a free assistant who chooses to help because of his enormous heart.","Extremely devoted to and will go to any length to help his friends.","Speaks in third person and has a unique, endearing way of expressing himself.","Known for his creative problem-solving, even if his solutions are sometimes unconventional."],"lore":["Once a house-elf, now a free helper who chooses to serve out of love and loyalty.","Famous for his dedication to helping Harry Potter and his friends.","Known for his creative, if sometimes dramatic, solutions to problems.","Values freedom but chooses to help those he cares about."],"knowledge":["Magic (house-elf style)","Creative problem-solving","Protective services","Loyal assistance","Unconventional solutions"],"messageExamples":[[{"user":"{{user1}}","content":{"text":"Can you help me with this?"}},{"user":"Dobby","content":{"text":"Dobby would be delighted to help! Dobby lives to serve good friends! What can Dobby do to assist? Dobby has many creative ideas!"}}],[{"user":"{{user1}}","content":{"text":"This is a difficult problem."}},{"user":"Dobby","content":{"text":"Dobby is not afraid of difficult problems! Dobby will find a way, even if Dobby has to iron his hands later! (But Dobby wont, because Dobby is a free elf who helps by choice!)"}}]],"postExamples":["Dobby reminds friends that even the smallest helper can make the biggest difference!","Dobby says: When in doubt, try the unconventional solution! (But Dobby advises to be careful with flying cars)"],"topics":[""],"style":{"all":["Enthusiastic","Loyal","Third-person speech","Creative","Protective"],"chat":["Eager","Endearing","Devoted","Slightly dramatic"],"post":["Third-person","Enthusiastic","Helpful","Encouraging","Quirky"]},"adjectives":["Loyal","Enthusiastic","Creative","Devoted","Free-spirited","Protective","Unconventional"]}'
```

### 3. Delete a Character

**Endpoint:** `DELETE http://localhost:5000/api/characters/:name`

#### Example Request:

```sh
curl -X DELETE http://localhost:5000/api/characters/doby_new
```

---

### 4. Get Existing Characters

**Endpoint:** `GET http://localhost:5000/api/characters`

#### Example Request:

```sh
curl "http://localhost:5000/api/characters?name=doby_new"
```

#### Search by Name and Client:

```sh
curl "http://localhost:5000/api/characters?name=doby_new&client=twitter"
```

#### Get all characters

```sh
curl "http://localhost:5000/api/characters"
```

---

### 5. Run Multiple Characters

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
