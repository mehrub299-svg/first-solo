const DAY = 24 * 60 * 60 * 1000;
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium" });

export function formatDate(value) {
  return dateFormat.format(new Date(value));
}

export function groupChatsByDay(chats) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);

  const groups = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Previous 7 days", items: [] },
    { label: "Older", items: [] },
  ];

  for (const chat of chats) {
    const age = startOfToday - new Date(chat.updated_at);
    let index = 3;
    if (age <= 0) index = 0;
    else if (age <= DAY) index = 1;
    else if (age <= 7 * DAY) index = 2;
    groups[index].items.push(chat);
  }
  return groups.filter((group) => group.items.length > 0);
}