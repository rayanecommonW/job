-- Close managed T3 panel tabs. window.close() does not remove these tabs.
-- Run only while the intended career thread and its right panel are visible.
-- Usage: osascript scripts/close-career-browser-tabs.applescript <first-tab-title> <all|others>
-- The caller must archive URLs, answers and receipts before invoking this tool.
on taskFindDescription(taskNode, taskPrefix, taskDepth)
 tell application "System Events"
  try
   if description of taskNode starts with taskPrefix then return taskNode
   if taskDepth > 0 then
    repeat with taskChild in UI elements of taskNode
     set taskFound to my taskFindDescription(taskChild, taskPrefix, taskDepth - 1)
     if taskFound is not missing value then return taskFound
    end repeat
   end if
  end try
 end tell
 return missing value
end taskFindDescription

on run taskArgs
 if (count of taskArgs) is not 2 then error "Supply the expected first tab title and all or others"
 set taskExpectedTitle to item 1 of taskArgs
 set taskMode to item 2 of taskArgs
 if taskMode is "all" then
  set taskMenuLabel to "Close all"
 else if taskMode is "others" then
  set taskMenuLabel to "Close others"
 else
  error "Unknown closure mode"
 end if
 tell application "System Events" to tell process "T3 Code (Alpha)"
  set taskRoot to window 1
  repeat with taskIndex from 1 to 7
   set taskRoot to UI element 1 of taskRoot
  end repeat
  set taskFrame to taskRoot
  repeat with taskIndex in {1, 1, 3, 1}
   set taskFrame to UI element taskIndex of taskFrame
  end repeat
  set taskThreadHeader to missing value
  repeat with taskIndex from 1 to 2
   if taskThreadHeader is missing value then set taskThreadHeader to my taskFindDescription(UI element taskIndex of taskFrame, "Thread actions for ", 5)
  end repeat
  if taskThreadHeader is missing value then error "Visible thread header unavailable; no tabs closed"
  if description of taskThreadHeader does not start with "Thread actions for start applying you can start with start here" and description of taskThreadHeader does not start with "Thread actions for in Documents create a new repo called career autom" then error "The visible thread is not an authorized career thread; no tabs closed"
  set taskPanelToggle to my taskFindDescription(UI element 1 of taskFrame, "Toggle right panel", 5)
  if taskPanelToggle is missing value then error "Panel toggle unavailable; no tabs closed"
  if value of taskPanelToggle is 0 then
   perform action "AXPress" of taskPanelToggle
   delay 0.2
  end if
  repeat with taskIndex in {1, 1, 3, 1, 4, 2, 2}
   set taskRoot to UI element taskIndex of taskRoot
  end repeat
  if name of taskRoot is not taskExpectedTitle then error "First panel tab differs from the archived inventory; no tabs closed"
  perform action "AXShowMenu" of taskRoot
  delay 0.15
  -- Keep generic references. Resolving AXMenu to a named menu breaks lookup.
  set taskLabels to name of UI elements of UI element 2 of window 1
  repeat with taskIndex from 1 to count of taskLabels
   if item taskIndex of taskLabels is taskMenuLabel then
    perform action "AXPress" of UI element taskIndex of UI element 2 of window 1
    return "Requested managed-tab closure: " & taskMenuLabel
   end if
  end repeat
  error "Closure menu item unavailable; no tabs closed"
 end tell
end run
