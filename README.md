# 📦 LocalLibSync

**LocalLibSync** is your all-in-one desktop tool for building and syncing Angular (or any Node-based) libraries across multiple local projects—**instantly**, **visually**, and **without the hassle**.

---

## ✨ Features

- 🚀 **One-Click Build & Sync**  
  Build your library and sync it to all your local projects with a single click.

- 🖥️ **Modern GUI**  
  Forget the terminal—manage everything from an intuitive, streamlined interface.

- 🗂️ **Multiple Sync Destinations**  
  Add unlimited sync targets. Edit or remove them anytime with ease.

- 🛠️ **Custom Build Commands**  
  Compatible with any build tool—just enter your command (e.g., `ng build`, `npm run build`, etc.).

- 🔄 **Live Feedback**  
  Get real-time logs and sync progress, so you’re always in the loop.

- ⚙️ **Effortless Setup**  
  No messy config files. Just point, click, and sync.

---

## ❓ Why LocalLibSync?

If you're tired of:

- Manually copying build outputs 🔁  
- Constantly running the same scripts ⚙️  
- Wondering which project has the latest version 🤔  

**LocalLibSync** is your time-saving solution. Maintain clean, up-to-date local dependencies across projects without breaking a sweat.

---

## 🧩 How It Works

### 1. Add Your Library

- Click the ➕ **Add New Project** button
- Enter:
  - Library name  
  - Source folder  
  - Build output folder  
  - Build command (e.g., `ng build my-lib`)  
  - One or more destination folders
- Click **Save**

### 2. Edit or Update Projects

- Click the ✏️ **Edit** icon next to a project to update details or destinations.

### 3. Build & Sync

- Click the 🔄 **Sync** button  
- LocalLibSync will:
  - Run your build command  
  - Copy the output to all defined destinations  
  - Show progress and logs live

### 4. Review Logs

- Use the **Log Output** panel to confirm successful builds and troubleshoot if needed.

### 5. Repeat As Needed

- Add, edit, remove projects or destinations anytime.  
- Sync as often as needed—no limitations.

---

## 💡 Tips

- Test your build command manually in the terminal before entering it in LocalLibSync.
- For Angular projects, the command is usually:

  ```bash
  ng build <your-lib-name>
