-- Close archived career tabs and restore whichever thread the user was viewing.
on taskFind(taskNode, taskPrefix, taskRole, taskDepth)
 tell application "System Events"
  try
   if description of taskNode starts with taskPrefix then
    if taskRole is "" or role of taskNode is taskRole then return taskNode
   end if
   if taskDepth > 0 then
    repeat with taskChild in UI elements of taskNode
     set taskFound to my taskFind(taskChild, taskPrefix, taskRole, taskDepth - 1)
     if taskFound is not missing value then return taskFound
    end repeat
   end if
  end try
 end tell
 return missing value
end taskFind

on run taskArgs
 if (count of taskArgs) is not 2 then error "Supply archived tab title and closure mode"
 tell application "System Events" to tell process "T3 Code (Alpha)" to set taskRoot to window 1
 set taskHeader to my taskFind(taskRoot, "Thread actions for ", "", 16)
 if taskHeader is missing value then error "Current thread header unavailable"
 tell application "System Events" to set taskHeaderText to description of taskHeader
 set taskRestore to missing value
 if taskHeaderText does not start with "Thread actions for start applying you can start with start here" then
  set taskOriginalPrefix to text 20 thru 49 of taskHeaderText
  set taskRestore to my taskFind(taskRoot, taskOriginalPrefix, "AXButton", 16)
  if taskRestore is missing value then error "Cannot preserve original thread; no tabs closed"
  set taskCareer to my taskFind(taskRoot, "start applying you can start with start here", "AXButton", 16)
  if taskCareer is missing value then error "Career thread unavailable; no tabs closed"
  tell application "System Events" to perform action "AXPress" of taskCareer
  delay 0.15
 end if
 try
  set taskResult to do shell script "osascript scripts/close-career-browser-tabs.applescript " & quoted form of item 1 of taskArgs & " " & quoted form of item 2 of taskArgs
 on error taskMessage number taskNumber
  if taskRestore is not missing value then
   tell application "System Events" to perform action "AXPress" of taskRestore
  end if
  error taskMessage number taskNumber
 end try
 if taskRestore is not missing value then
  tell application "System Events" to perform action "AXPress" of taskRestore
 end if
 return taskResult
end run
