
#import sys; sys.path.append("/home/mmccoo/kicad/kicad_mmccoo/python_usage_tracker"); import kicad_python_usage_tracker

#import pcbnew; b = pcbnew.GetBoard(); b.Add()


import pcbnew
import types
import inspect
import pdb
import numbers

stats = {}
method_stats = {}
returned_vals = {}
returned_ids = {}

board = None

file = open("test.py", "w")
file.write("import pcbnew\n\n")

def format_args(args):
    toprint = []

    for arg in args:

        strval = str(arg)
        if (strval in returned_vals):
            toprint.append(returned_vals[strval])
            continue

        if (isinstance(arg, numbers.Number)):
            toprint.append(str(arg))
            continue

        # I believe that checking src and unicode is better than checking basestring because
        # basestring won't work in python 3.0
        if (isinstance(arg, pcbnew.wxString) or isinstance(arg, str) or isinstance(arg, unicode)):
            toprint.append("\"" + str(arg) + "\"")
            continue

        print("other type {}".format(arg))
        toprint.append(str(arg))

    inprint = False
    return (", ".join(toprint))

def format_retval(val):
    strval = str(val)

    if (isinstance(val, numbers.Number)):
        return (True, strval)

    if (isinstance(val, unicode)):
        return (True, "\"" + strval + "\"")

    if (isinstance(val, pcbnew.wxString)):
        return (True, "\"" + str(val) + "\"")

    if (hasattr(val, "__module__") and (val.__module__ != "pcbnew")):
        return (True, strval)

    if (strval in returned_vals):
        return (False, returned_vals[strval])

    idx = returned_ids[val.__class__.__name__] = returned_ids.setdefault(val.__class__.__name__, -1) + 1
    retval = returned_vals[strval] = str(val.__class__.__name__) + "_" + str(idx)

    return (False, retval)


def track_fn(func, name):
    def call(*args, **kwargs):

        global intrack
        intrack = intrack + 1

        result = func(*args, **kwargs)

        if (intrack == 1):
            stats[name] = stats.setdefault(name, 0) + 1

            argsstr = format_args(args)
            isconst, retstr = format_retval(result)

            callingframe = inspect.stack()[1]

            if (isconst):
                file.write("assert({} == {}({})) # {}, {}\n".format(retstr, name, argsstr, callingframe[1], callingframe[2]))
            else:
                file.write("{} = {}({}) # {}, {}\n".format(retstr, name, argsstr, callingframe[1], callingframe[2]))

        intrack = intrack - 1

        return result
    return call

intrack = 0
incrnum = 0
mynum = 0
def track_method(m, pathtohere, name):
    def call(*args, **kwargs):

        # printing calls str which may call other methods.
        # can't just use true/false, because printing (__str__) can trigger
        # more method calls.
        # also, need to be careful
        global intrack
        intrack = intrack + 1

        global incrnum
        incrnum = incrnum + 1

        global mynum

        # there are cases when python uses exceptions like out of range exception
        # as a way to know when to stop a loop.
        # getitem is one of the methods that I'm wrapping (like to get a net from a nettable)
        # for other methods, like wxPoint.__getitem__, I need to be sure to let the out of range
        # exception propagate. I also need to do some cleanup.
        try:
            result = m(*args, **kwargs)
        except Exception, e:
            intrack = intrack - 1
            raise
        #pdb.set_trace()
        #print("exception {}".format(str(e)))


        if (intrack == 1):
            callingframe = inspect.stack()[1]

            instclass = args[0].__class__
            tbl = method_stats.setdefault(pathtohere + "." + name, {})
            tbl[instclass] = tbl.setdefault(instclass, 0) + 1

            constself, slf = format_retval(args[0])
            argsstr = format_args(args[1:])

            isconst, retstr = format_retval(result)

            isconstructor = (name == "__init__")
            if (isconstructor):
                # constructor/__init__ doesn't return a value. The call to the constructor looks like
                # a method call, but it's syntactic sugar around the self that is passed around.
                file.write("{} = {}({}) # {}, {}\n".format(slf, pathtohere, argsstr, callingframe[1], callingframe[2]))
            elif (result is None):
                # it's important to do result is None instead of result == None because the equality
                # operator for result will expect None to be of its type.
                file.write("{}.{}({}) # {}, {}\n".format(slf, name, argsstr, callingframe[1], callingframe[2]))
            elif (isconst):
                file.write("assert({} == {}.{}({})) # {}, {}\n".format(retstr, slf, name, argsstr, callingframe[1], callingframe[2]))
            else:
                file.write("{} = {}.{}({}) # {}, {}\n".format(retstr, slf, name, argsstr, callingframe[1], callingframe[2]))

        intrack = intrack - 1
        return result
    return call


def track_class(pathtohere, obj):
    pathtohere = pathtohere + "." + obj.__name__

    if (obj.__name__ == 'ActionPlugin'):
            return

    for name in obj.__dict__:
        #if ((name[0] == "_") and (name != "__init__")):
        if ((name == "__del__") or (name == "__str__") or (name == "__repr__")):
            continue

        # if getattr is wrapped, something goes wrong when called from within __init__
        # somewhere, I'm doing something with a not full constructed object.
        # I haven't taken the time to track it down.
        if (name == "__getattr__"):
            continue

        item = getattr(obj, name)
        if inspect.ismethod(item):
            setattr(obj, name, track_method(item, pathtohere, name))



module = pcbnew
for name in dir(module):
    if (name[0] == "_"):
        continue

    obj = getattr(module, name)
    if inspect.isclass(obj):
        track_class(module.__name__, obj)

    elif (inspect.ismethod(obj) or inspect.isfunction(obj)):
        setattr(pcbnew, name, track_fn(obj, module.__name__ + "." + name))

    elif inspect.isbuiltin(obj):
        pass

    else:
        #print("other {}".format(name))
        pass

def report_usage():
    for k in stats:
        if (stats[k] == 0):
            continue;
        print("{} {}". format(k, stats[k]))
