# Zelda64 Instrument Bank Creator
A python-based Zelda64 instrument bank creator, editor, and compiler with a fluent user interface.

## TODO
> [!IMPORTANT]
> This is not an exhaustive list of planned features and functionality of the app. This TODO list is a way to keep track of what has and hasn't been implemented in order to release version 1.0.0 of the app.
### Structure Functionality
- [x] Load user-defined structure presets
- [x] Create empty user-defined structure presets
- [x] Create user-defined structure presets from built-in structure
- [x] Export user-defined structure presets
- [x] Delete user-defined structure presets
- [ ] Modify user-defined structure preset parameters (All but samples and envelopes)
- [x] Modify user-defined structure preset sample assignment
- [x] Modify user-defined structure preset envelope assignment
### Instrument Bank Functionality
- [x] Load user-defined instrument bank presets
- [x] Create empty user-defined instrument bank presets
- [x] Drumkit selection during empty user-defined instrument bank preset creation
- [x] Create instrument bank presets from built-in instrument bank
- [x] Export user-defined instrument bank presets
- [x] Delete user-defined instrument bank presets
- [x] Modify user-defined instrument bank preset table entry data
- [x] Modify user-defined instrument bank preset structure assignment
- [x] Compile user-defined instrument bank presets to binary
### Drumkit Functionality
- [ ] Load user-defined drumkit presets
- [ ] Create empty user-defined drumkit presets
- [ ] Create user-defined drumkit presets from built-in drumkit
- [ ] Export user-defined drumkit presets
- [ ] Delete user-defined drumkit presets
- [ ] Modify user-defined drumkit preset drum assignment
### App Functionality
- [x] Change default output folder location
- [x] Change default preset folder location
- [x] Implement keyboard shortcuts
- [x] Implement copying user-defined presets
- [x] Implement pasting user-defined presets
- [x] implement undoing pasting of user-defined presets
- [x] Implement undoing creation of user-defined structure presets
- [x] Implement redoing creation of user-defined structure presets
- [x] Implement undoing changes made to user-defined structure presets
- [x] Implement redoing changes made to user-defined structure presets
- [x] Implement undoing deletion of user-defined structure presets
- [x] Implement redoing deletion of user-defined structure presets
- [x] Implement undoing creation of user-defined instrument bank presets
- [x] Implement redoing creation of user-defined instrument bank presets
- [x] Implement undoing changes made to user-defined instrument bank presets
- [x] Implement redoing changes made to user-defined instrument bank presets
- [x] Implement undoing deletion of user-defined instrument bank presets
- [x] Implement redoing deletion of user-defined instrument bank presets
- [ ] Implament undoing creation of user-defined drumkit presets
- [ ] Implement redoing creation of user-defined drumkit presets
- [ ] Implement undoing changes made to user-defined drumkit presets
- [ ] Implement redoing changes made to user-defined drumkit presets
- [ ] Implement undoing deletion of user-defined drumkit presets
- [ ] Implement redoing deletion of user-defined drumkit presets
- [ ] Add home page . . .
- [x] Add banks page where users can create, modify, export, delete, and compile instrument bank presets
- [x] Add presets page where users can create, modify, export, and delete structure presets
- [ ] Add drumkits page where users can create, modify, export, and delete drumkit presets
- [ ] Add pop-up if the app encounters and error
### Internal App Data
- [ ] Implement built-in instrument presets (Majora's Mask done)
- [ ] Implement built-in drum presets
- [ ] Implement built-in effect presets (Unlikely to ever be done)
- [ ] Implement built-in sample presets (Majora's Mask done)
- [x] Implement built-in envelope presets
- [ ] Implement built-in instrument bank presets
- [ ] Implement built-in drumkit presets
- [x] Add handling for built-in sample preset VROM addresses

### Keyboard Shortcuts
> [!IMPORTANT]
> Follow-up key sequence combos (`Ctrl+<Key>, <Key>`) require you to input the initial sequence, release all keys, then input the follow up key or sequence.

| Key Sequence | Description |
| --- | --- |
| `Ctrl+N` | Opens the dialog to create an empty user-defined preset |
| `Ctrl+Shift+N` | Opens the dialog to create a user-defined preset from a built-in preset |
| `Ctrl+E, P` | Opens the dialog to edit a user-defined structure preset's parameters |
| `Ctrl+E, S` | Opens the dialog to edit a user-defined structure preset's sample assignment |
| `Ctrl+E, E` | Opens the dialog to edit a user-defined structure preset's envelope assignment |
| `Ctrl+E, M` | Opens the dialog to edit a user-defined instrument bank preset's table entry data |
| `Ctrl+E, I` | Opens the dialog to edit a user-defined instrument bank preset's instrument assignment |
| `Ctrl+E, D` | Opens the dialog to edit a user-defined instrument bank preset's drum assignment |
| `Ctrl+E, E` | Opens the dialog to edit a user-defined instrument bank preset's effect assignment |
| `Ctrl+Z` | Undo the last edit made to a user-defined preset (page dependent) |
| `Ctrl+Y` | Redo the last edit made to a user-defined preset (page dependent) |
| `Ctrl+C` | Copy the selected user-defined preset(s) |
| `Ctrl+V` | Paste the selected user-defined preset(s) |
| `Ctrl+S` | Open the dialog to save the user-defined preset to disk as a YAML file |
| `Ctrl+B` | Compile the selected instrument bank preset(s) to binary |
| `Del` | Delete the selected user-defined preset(s) from disk |
