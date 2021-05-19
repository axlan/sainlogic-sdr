INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_SAINLOGIC sainlogic)

FIND_PATH(
    SAINLOGIC_INCLUDE_DIRS
    NAMES sainlogic/api.h
    HINTS $ENV{SAINLOGIC_DIR}/include
        ${PC_SAINLOGIC_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    SAINLOGIC_LIBRARIES
    NAMES gnuradio-sainlogic
    HINTS $ENV{SAINLOGIC_DIR}/lib
        ${PC_SAINLOGIC_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/sainlogicTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(SAINLOGIC DEFAULT_MSG SAINLOGIC_LIBRARIES SAINLOGIC_INCLUDE_DIRS)
MARK_AS_ADVANCED(SAINLOGIC_LIBRARIES SAINLOGIC_INCLUDE_DIRS)
