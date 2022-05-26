# NotePublisher
```
Usage:
  cli <configfile> <output_path>> [--stack=STRING] [--notebook=STRING] [--formats=PATTERNS]
  cli --version

Options:
  -h --help  show this help message and exit
  --version  show version and exit
  -v --verbose  print status messages
  --stack=STRING  string to match stack names against when searching
  --notebook=STRING  string to match notebook names against when searching
  --formats=PATTERNS   export notes to file formats which match these comma
                       separated patterns [default: html,enex]

```

## Evernote API Keys
To use, you'll need production API keys from Evernote.  Enter your keys into a JSON config file similar to this one:
```
{
   "output" : "/Users/testuser/Documents/NotePublisher",
   "consumer_key" : "yyyyyyyyyyyyy",
   "consumer_secret": "zzzzzzzzzzzzzzzzzzzzzzzz",
   "dev_auth_token": "zzzzzzzzzzzzzzzzzzzzzzzzyyyyyyyyyyyyyyyyyyyyyyyyyyzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
}
```


