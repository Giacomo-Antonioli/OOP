import time

from alive_progress import alive_bar

letters = [chr(ord('A') + x) for x in range(26)]
with alive_bar(26, bar="bubbles", dual_line=True, title='Alphabet') as bar:
    for c in letters:
        bar.text = f'-> Teaching the letter: {c}, please wait...'
        if c in 'HKWZ':
            print(f'fail "{c}", retry later')
        time.sleep(0.3)
        bar(10)
