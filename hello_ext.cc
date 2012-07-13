#include <boost/python.hpp>
#include <string>

//using namespace std;
char const* greet()
{
     return "hello, world";
}

struct Hello {
  std::string hi() {
    return "hi there";
  }
};

BOOST_PYTHON_MODULE(hello_ext)
{
    using namespace boost::python;
    def("greet", greet);

    class_<Hello>("Hello")
      .def("hi", &Hello::hi)
    ;
}
