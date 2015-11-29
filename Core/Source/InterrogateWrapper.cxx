
#include "dtoolbase.h"
#include "interrogate_request.h"

#undef _POSIX_C_SOURCE
#include "py_panda.h"

extern LibraryDef RSCoreModules_moddef;
extern void Dtool_RSCoreModules_RegisterTypes();
extern void Dtool_RSCoreModules_ResolveExternals();
extern void Dtool_RSCoreModules_BuildInstants(PyObject *module);

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef py_RSCoreModules_module = {
  PyModuleDef_HEAD_INIT,
  "RSCoreModules",
  NULL,
  -1,
  NULL,
  NULL, NULL, NULL, NULL
};

#ifdef _WIN32
extern "C" __declspec(dllexport) PyObject *PyInit_RSCoreModules();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) PyObject *PyInit_RSCoreModules();
#else
extern "C" PyObject *PyInit_RSCoreModules();
#endif

PyObject *PyInit_RSCoreModules() {
  Dtool_RSCoreModules_RegisterTypes();
  Dtool_RSCoreModules_ResolveExternals();

  LibraryDef *defs[] = {&RSCoreModules_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, &py_RSCoreModules_module);
  if (module != NULL) {
    Dtool_RSCoreModules_BuildInstants(module);
  }
  return module;
}

#else  // Python 2 case

#ifdef _WIN32
extern "C" __declspec(dllexport) void initRSCoreModules();
#elif __GNUC__ >= 4
extern "C" __attribute__((visibility("default"))) void initRSCoreModules();
#else
extern "C" void initRSCoreModules();
#endif

void initRSCoreModules() {
  Dtool_RSCoreModules_RegisterTypes();
  Dtool_RSCoreModules_ResolveExternals();

  LibraryDef *defs[] = {&RSCoreModules_moddef, NULL};

  PyObject *module = Dtool_PyModuleInitHelper(defs, "RSCoreModules");
  if (module != NULL) {
    Dtool_RSCoreModules_BuildInstants(module);
  }
}
#endif

