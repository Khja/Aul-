import re

def change(values, word, abbr={}):
    form, before, what, after, mutation = values
    # Replace abbreviations with their values
    l = [form, before, what, after, mutation]
    for i in range(len(l)):
        for j in abbr:
             l[i] = l[i].replace(j, abbr[j])
    form, before, what, after, mutation = l[0], l[1], l[2], l[3], l[4]

    # Compile regex
    form = re.compile(form)
    before = f"(?<={before})"
    after = f"(?={after})"
    what = re.compile(f"{before}{what}{after}")

    # If the form is accepted
    if form.search(word) != None:
        # Change 'what' to 'mutation' if it can
        changed = what.sub(mutation, word)
        return changed
    else:
        return word

# Example
# Changes 'ts' to 'ps' when after a vowel and an 'm', if there is another vowel afterwards.
# namtsen > nampsen

# vowel = r'[aeiou]'
# consonant = r'[qwrtpsdfghjklxczvbnm]'

# abbr = {'[V]':vowel, '[C]':consonant}

# form = r""
# before = r"[V]m"
# after = r"[V]"
# what = r"ts"
# to = r"ps"

# s = change(form, before, what, after, to, 'namtsen', abbr)
# print(s)

# s0 = change("", "", " ", "", "e", ' hepo')
# print(s0)
# s1 = change("", r"\b", "ehe", "", "hee", s0)
# print(s1)
# s2 = change("", r"", "ee", "", "ei", s1)
# print(s2)
# s3 = change('', r'', r'$', r"", 'men', s2)
# print(s3)
