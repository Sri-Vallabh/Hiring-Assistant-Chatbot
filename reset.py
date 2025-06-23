import sqlite3

def clear_all_tables():
    conn = sqlite3.connect('talentscout_candidates.db')
    cursor = conn.cursor()
    
    # Display 5 entries from candidates
    print('Sample entries from candidates:')
    try:
        cursor.execute('SELECT * FROM candidates LIMIT 5')
        candidates_sample = cursor.fetchall()
        for row in candidates_sample:
            print(row)
    except Exception as e:
        print("Error fetching from candidates:", e)
    
    # Display 5 entries from question_ratings
    print('\nSample entries from question_ratings:')
    try:
        cursor.execute('SELECT * FROM question_ratings LIMIT 5')
        question_ratings_sample = cursor.fetchall()
        for row in question_ratings_sample:
            print(row)
    except Exception as e:
        print("Error fetching from question_ratings:", e)
    
    # Delete all records (delete question_ratings first due to foreign key)
    try:
        cursor.execute('DELETE FROM question_ratings')
        cursor.execute('DELETE FROM candidates')
        conn.commit()
        print('\nAll records have been deleted from all tables.')
    except Exception as e:
        print("Error deleting records:", e)
    finally:
        conn.close()

if __name__ == '__main__':
    clear_all_tables()
