from collections import defaultdict, namedtuple

class TagList:
    def __init__(self):
        self.stack = []
        self.tag_pos = []

    def append(self, value, closing = 0):
        if closing:
            if len(self.stack) > 0:
                self.tag_pos[self.stack.pop()].append(value)
            else:
                return -1
        else:
            self.stack.append(len(self.tag_pos))
            self.tag_pos.append([value])


class ErrorLog:
    def __init__(self, err_categories, text = None, context_range = 15):
        self.error_log = []
        self.err_categories = err_categories
        self.context_range = context_range
        self.text = text
    
    def log(self, category, start = None, end = None, error = ""):
        if start != None:
            if self.text == None:
                raise Exception("No text set")
            end = start if end == None else end
            start = max(start - self.context_range, 0)
            end = min(end + self.context_range + 1, len(self.text))
            error += self.text[start : end]
        if type(category) == int:
            self.error_log.append((self.err_categories[category], error))
        elif category not in self.err_categories:
            raise ValueError("Category is not valid")
        else:
            self.error_log.append((category, error))
    
    def __repr__(self):
        return self.error_log.__repr__()

    def show(self):
        msg = ""
        for error in self.error_log:
            msg += error[0] + ": " + error[1] + "\n"
        print(msg)


class Element:
    def __init__(self, name, start):
        self.name = name
        self.start = start
        self.end = start
        self.attributes = []
        self.classes = []
        self.content = ""
        self.children = []
    
    def __repr__(self):
        repr = "<" + self.name + ", " + str(self.start[0]) + ", "
        repr += "s" if self.end == self.start else "d"
        repr += ">"
        return repr


class Document():
    def __init__(self, format = None):
        self.format = format
        self.element_list = []
        self.element_dict = defaultdict(list)
    
    def add(self, element):
        self.element_list.append(element)
        self.element_dict[element.name].append(element)
    
    def select(self, name = None, post_index = None, index = None,
               content = None, elements = None):
        if name == None:
            selection = elements if elements != None else self.element_list
        else:
            if elements == None:
                if name in self.element_dict.keys():
                    selection = self.element_dict[name]
                else:
                    selection = None
            else:
                elements = [em for em in selection if em.name == name]
        if post_index != None:
            for n in range(len(selection)):
                if selection[n].start[0] >= post_index:
                    selection = selection[n:]
                    break
            else:
                selection = []
        if index != None:
            for element in selection:
                if element.end != None and index >= element.start and index < element.end:
                    selection = element
            else:
                selection = None
        elif content != None:
            selection = [em for em in selection if content in em.content]
        return selection
    
    def show(self, elem_list = False):
        if not elem_list:
            for key, value in self.element_dict.items():
                print(key + ": " + str(value))
        else:
            print(self.element_list)
    
    # to make: a sementic tree display
    
    def __repr__(self):
        return self.element_dict.__repr__()


class TextParser:
    def __init__(self, text, format = "HTML"):
        self.format = format
        if format != "HTML":
            raise Exception("Format not supported")

        self.text = text
        self.categories = ["Incomplete Tag", "Unpaired Closing Tag"]
        self.errors = ErrorLog(self.categories, text = text)
    
    def add_tag(self, start, end, document):
        keywords = self.text[start + 1: end - 1].split()
        name = keywords[0]
        if name[0] != '/':
            element = Element(name, (start, end))
            document.add(element)
        else:
            name = name[1:]
            for element in reversed(document.element_list):
                if element.start[0] >= end:
                    continue
                if element.name == name and element.end == element.start:
                    element.end = (start, end)
                    end = start
                    index = element.start[1]
                    while index < end:
                        sub_em = document.select(post_index=index)
                        if len(sub_em) == 0:
                            break
                        nxt_em = sub_em[0]
                        if nxt_em.end[1] <= end:
                            element.children.append(nxt_em)
                            element.content += self.text[index:nxt_em.start[0]]
                            index = nxt_em.end[1]
                        else:
                            break
                    if index < end:
                        element.content += self.text[index:end]
                    break
            else:
                self.errors.log(1, start, end)
    
    def parse_tags(self):
        text = self.text
        doc = Document(self.format)
        errors = self.errors

        opened = False
        start = 0
        for pos in range(len(text)):
            if text[pos] == '<':
                if opened:
                    errors.log(0, start = pos)
                else:
                    start = pos
                    opened = True
            if text[pos] == '>':
                if opened:
                    self.add_tag(start, pos + 1, doc)
                    opened = False
                else:
                    errors.log(0, start = pos)
        if opened == True:
            errors.log(0, start = start)

        return doc
