const Notes = require('apple-notes-jxa');
 
Notes.accounts()
  .then((accounts) => console.log(accounts.map((account) => if(account.name == 'iCloud') return account.id)));

//list the notes
