# Monkey

Easy Python monkey patching

Monkey aims to make it easy to import patched modules for testing or whatnot, it's designed
to be easy to use and to fix all the subtle problems monkey patched modules can cause by
making the patching explicit and keeping the patched modules out of the global namespace

## Monkey Patch a module

Suppose you want to import the `wackyzoom` module, but you want the `foo` method to always return *bar*

    import monkey

    def foo_patched(*args, **kwargs): return "bar"
    wackyzoom = monkey.patch('wackyzoom', foo=foo_patched)

    print wackyzoom.foo # prints "bar"

    # you can even import the original
    import wackyzoom as wz

    print wz.foo # will not be monkey patched, so will print whatever this made up func printed originally

That's all there is to it, at this moment, you can even go one level deep (I haven't tested deeper)

    wackyzoom = monkey.patch('wackyzoom', {"module.func": foo_patched})

    print wackyzoom.modul.func # prints "bar"
    
And you can pass in multiple things to patch:

    wackyzoom = monkey.patch('wackyzoom', {"module.func": foo_patched, "foo": foo_patched})

    print wackyzoom.foo # prints "bar"
    print wackyzoom.modul.func # prints "bar"

## Todo

Currently, Monkey doesn't handle imports that are done in a function, I've got some early code
on how to handle that did work, but it's currently disabled pending further testing and cleanup

I don't think it will work n levels deep, ie, I don't think I can patch `bar.baz.che` in `foo` yet

## Install

Use PIP

    pip install git+https://github.com/Jaymon/monkey#egg=monkey

## License

MIT I guess, use this code any way you want, if you extend it I'd love a pull request
so I can merge any new stuff in.

