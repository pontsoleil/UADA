import csv
import calendar

def create_calendar_csv(year, month, filename):
    # Get the number of days in the month and the first day of the week
    num_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]  # 0 = Monday, 6 = Sunday
    
    # Create a list of days for the month
    days = [str(i+1).zfill(2) for i in range(num_days)]
    
    # Initialize a list to hold the weeks, starting with padding if the month doesn't start on Sunday
    weeks = [[]]
    if first_weekday != 6:
        weeks[0] = [''] * (first_weekday + 1)
    
    # Populate the weeks with days
    for i, day in enumerate(days):
        if len(weeks[-1]) == 7:
            weeks.append([])  # Start a new week if the previous one is full
        weeks[-1].append(day)
    
    # Pad the last week with empty strings if necessary
    if len(weeks[-1]) < 7:
        weeks[-1].extend([''] * (7 - len(weeks[-1])))

    # Write to CSV file
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])  # Header row
        for week in weeks:
            csvwriter.writerow(week)

    print(f'CSV file {filename} created successfully.')

# Example usage
create_calendar_csv(2024, 1, 'calendar_2024_01.csv')
create_calendar_csv(2024, 2, 'calendar_2024_02.csv')

