const express = require('express');
const mongoose = require('mongoose');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

let childProcess = null; // Store the current running process

const app = express();

// Middleware for parsing JSON bodies
app.use(express.json());

// MongoDB Connection
const MONGO_URI = process.env.MONGO_URI || 'mongodb+srv://nathan:gFh8nOPl7Kp4MaMe@hackathon-mf.t8o5a.mongodb.net/?retryWrites=true&w=majority&appName=hackathon-mf';

mongoose.connect(MONGO_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

// // Character Schema
// const characterSchema = new mongoose.Schema({
//   name: {
//     type: String,
//     required: true,
//     unique: true
//   },
//   clients: [{
//     type: String
//   }],
//   modelProvider: {
//     type: String,
//     required: true
//   },
//   settings: {
//     secrets: {
//       type: Map,
//       of: String,
//       default: {}
//     },
//     voice: {
//       model: {
//         type: String
//       }
//     }
//   },
//   plugins: [{
//     type: String
//   }]
// });

// Flexible Character Schema - allows any fields
const characterSchema = new mongoose.Schema({}, { 
  strict: false,  // This allows fields that aren't defined in the schema
  strictQuery: false // This allows querying on fields that aren't defined in the schema
});

const Character = mongoose.model('Character', characterSchema);


// 1. add character to mongo
// ---------------------------

// POST endpoint to add a character
app.post('/api/characters', async (req, res) => {
  try {
    const characterData = req.body;
    const character = new Character(characterData);
    const savedCharacter = await character.save();
    res.status(201).json(savedCharacter);
  } catch (error) {
    if (error.code === 11000) { // Duplicate key error
      res.status(400).json({ error: 'Character with this name already exists' });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// 1.5 Delete character from mongo <todo>
// ---------------------------------------

// DELETE endpoint to remove a character by name
app.delete('/api/characters/:name', async (req, res) => {
  try {
    const { name } = req.params;
    
    const result = await Character.findOneAndDelete({ name });
    
    if (!result) {
      return res.status(404).json({ error: 'Character not found' });
    }
    
    res.json({ message: 'Character deleted successfully', character: result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 2. Get character data from mongo
// ---------------------------------

// GET endpoint to retrieve characters
app.get('/api/characters', async (req, res) => {
  try {
    const query = {};
    
    // Apply any filter from query parameters
    Object.keys(req.query).forEach(key => {
      if (key === 'name') {
        query.name = { $regex: req.query[key], $options: 'i' };
      } else if (Array.isArray(req.query[key])) {
        query[key] = { $in: req.query[key] };
      } else {
        query[key] = req.query[key];
      }
    });

    const characters = await Character.find(query);
    res.json(characters);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});



/*
// -------------------
// 3. Run characters
// -------------------

Working:

* get list of character names from api request
* get complete configs of character from mongo and save to individual files: characters/<character-name>.character.json
* stop previous child process if there is one
* run new child process in background: e.g. `pnpm start --characters="characters/doby_new.character.json"`;
*  Save run logs to `logs/` folder

*/
// Endpoint to run characters
app.post('/api/characters/run', async (req, res) => {
  try {
    const { characters } = req.body;
    
    if (!Array.isArray(characters) || characters.length === 0) {
      return res.status(400).json({ error: 'Invalid characters list' });
    }

    // Ensure characters directory exists
    const charactersDir = path.join(__dirname, 'characters');
    await fs.mkdir(charactersDir, { recursive: true });

    // Array to store character file paths
    const characterFiles = [];

    // Fetch and save character data
    for (const characterName of characters) {
      const character = await Character.findOne({ name: characterName });
      
      if (!character) {
        console.warn(`Character ${characterName} not found in database`);
        continue;
      }

      const filePath = path.join(charactersDir, `${characterName}.character.json`);
      await fs.writeFile(filePath, JSON.stringify(character, null, 2));
      characterFiles.push(filePath);
    }

    // Check if we have any character files to run
    if (characterFiles.length === 0) {
      return res.status(404).json({ error: 'No characters found to run' });
    }

    // Construct character file paths for command
    const characterFilesArg = characterFiles.map(f => path.relative(__dirname, f)).join(', ');
    console.log("Character files arg:", characterFilesArg);

    // Kill the previous process if running
    if (childProcess) {
      console.log("Stopping previous character process...");
      childProcess.kill();
      childProcess = null;
    }

    // Run the character code
    const runCommand = `pnpm start --characters="${characterFilesArg}"`;
    const logFilePath = path.join(__dirname, 'logs', 'character_run.log');

    // Ensure logs directory exists
    await fs.mkdir(path.dirname(logFilePath), { recursive: true });

    childProcess = exec(runCommand);

    // Stream logs to a file
    const logStream = await fs.open(logFilePath, 'a');
    childProcess.stdout.on('data', (data) => logStream.write(`[STDOUT] ${data}`));
    childProcess.stderr.on('data', (data) => logStream.write(`[STDERR] ${data}`));

    // Handle process exit
    childProcess.on('exit', (code) => {
      logStream.write(`\nProcess exited with code: ${code}\n`);
      logStream.close();
      childProcess = null;
    });

    // Return response immediately
    res.json({
      message: 'Characters run successfully',
      characters: characterFiles,
      logFile: logFilePath,
      characterFilesArg: characterFilesArg
    });

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// --------------------------
// Error handling middleware
// --------------------------
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// ---------------------
// Run the express_app
// ---------------------
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});