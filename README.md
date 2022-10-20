## GitSlice

This project is part of CSC4006 (Research and Development Project).

GitSlice is a tool to iterate through commits in a Git repository, performing
some action(s) at each commit.

At present the tool will loop through each commit and display the files and 
directories which existed in the root of the repository at that commit.

Here is some sample output from the tool at `34f21121`:

```
INFO:root:
 ________  ___  _________  ________  ___       ___  ________  _______      
|\   ____\|\  \|\___   ___\   ____\|\  \     |\  \|\   ____\|\  ___ \     
\ \  \___|\ \  \|___ \  \_\ \  \___|\ \  \    \ \  \ \  \___|\ \   __/|    
 \ \  \  __\ \  \   \ \  \ \ \_____  \ \  \    \ \  \ \  \    \ \  \_|/__  
  \ \  \|\  \ \  \   \ \  \ \|____|\  \ \  \____\ \  \ \  \____\ \  \_|\ \ 
   \ \_______\ \__\   \ \__\  ____\_\  \ \_______\ \__\ \_______\ \_______\
    \|_______|\|__|    \|__| |\_________\|_______|\|__|\|_______|\|_______|
                             \|_________|                                  

INFO:root:Runtime information:
INFO:root:  OS version: 		win32
INFO:root:  Python version: 	3.10.4 (tags/v3.10.4:9d38120, Mar 23 2022, 23:13:41) [MSC v.1929 64 bit (AMD64)]
INFO:root:  GitPython version: 	3.1.29
INFO:root:  Working directory: 	C:/Users/dylan/OneDrive/Documents/Projects/PyCharm/csc4006-project-testing-repo
INFO:root:  Logging level: 		20
INFO:root:
INFO:root:Current branch is main
INFO:root:
INFO:root:Checking out commit f74470490cd644093349452a69d8aa15614625cd (Commit C)
INFO:root:Listing files in directory:
INFO:root: > .git, A.txt, B.txt, C.txt
INFO:root:
INFO:root:Checking out commit 5059c4a9f306dcc0e56ef3c46db459202e63bfa7 (Commit B)
INFO:root:Listing files in directory:
INFO:root: > .git, A.txt, B.txt
INFO:root:
INFO:root:Checking out commit 0d41551eed506bbdd5a0d35de9cea93308bfb0eb (Commit A)
INFO:root:Listing files in directory:
INFO:root: > .git, A.txt
INFO:root:
INFO:root:Restoring original branch (main)
```
