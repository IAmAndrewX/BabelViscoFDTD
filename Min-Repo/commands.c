#include <Python.h>
#include "numpy/ndarraytypes.h"
#include "numpy/ufuncobject.h"
#include "numpy/npy_3kcompat.h"



extern char* metalswift_add();


// Good stuff: https://numpy.org/doc/stable/reference/c-api/array.html
// Adapted from: https://gist.github.com/kanhua/8f1eb7c67f5a031633121b6b187b8dc9
static PyObject* addition(PyObject *self, PyObject *args){

    PyArrayObject *arr1, *arr2;
    // http://web.mit.edu/people/amliu/vrut/python/ext/parseTuple.html
    PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &arr1, &PyArray_Type, &arr2);
    
    printf("This is the start of the addition module! \n");
    
    printf("Checking dimensions, size, etc. to ensure addition can be done...\n\n");

    printf("Testing Number of Dimensions...\n");

    npy_intp dims[3]; // Creating the stride array
    
    npy_intp dummy = PyArray_NDIM(arr1);
    if(dummy != PyArray_NDIM(arr2)){
        printf("Your arrays don't have the same number of dimensions!\n\n");
        Py_RETURN_NONE;
    }
    else{
        printf("Number of Dimensions Correct!\n\n");
    }
    
    printf("Testing dimension shape!\n"); // Also inputting strides
    for(int i=0; i<dummy; i++) {
        npy_intp *dummy2 = PyArray_DIM(arr1, i);
        if(dummy2 != PyArray_DIM(arr2, i)){
            i = i + 1;
            printf("Your arrays don't have the same shape at dimension %o!", i);
            Py_RETURN_NONE;
        }
        dims[i] = dummy2;
    }
    printf("Dimension shapes match up!\n\n");

    printf("Catching other errors (assuming 3rd dimension) via checking dimension sizes...\n");
    npy_intp *size = PyArray_Size(arr1);
    if(size != PyArray_Size(arr2)){
        printf("Something is wrong in your arrays that are making them unequal in size. \n\n");
        Py_RETURN_NONE;
    }
    
    // Alignment may be needed in the future but just for the sake of time it's not implemented.
    printf("Args check successful! Checking array alignment...\n\n"); 
    if(PyArray_IS_C_CONTIGUOUS(arr1) == 0){
        printf("NOT A GOOD ARRAY :(");
    }
    else{
        printf("GOOD ARRAY :) \n");
    }
    
    printf("Sending data to Swift...\n");
    char *data1 = PyArray_DATA(arr1);
    printf("Data 1 Memory address: %p\n", data1);    
    char *data2 = PyArray_DATA(arr2);
    printf("Data 2 Memory address: %p\n\n", data2);    

    // Takes in the two arrays, returns a pointer to flat array of processed data.

    char *output = metalswift_add(data1, data2, size);

    PyArray_Descr *descr =  PyArray_DescrNewFromType(NPY_FLOAT);
    PyObject *outarray = PyArray_NewFromDescr(&PyArray_Type, descr, dummy, dims, NULL,
                                        output, NPY_ARRAY_WRITEABLE, NULL);


    return outarray;
    // return PyArray_Return(answer);
    
}

static PyMethodDef myMethods[] = {
    
    
    {
        "addition", addition, METH_VARARGS,
        "addition function test",
    },
    { NULL, NULL, 0, NULL }

};

static struct PyModuleDef myModule = {
    PyModuleDef_HEAD_INIT,
    "myModule",
    "Test Module",
    -1,
    myMethods
};

PyMODINIT_FUNC PyInit_myModule(void)
{
    Py_Initialize();
    import_array();
    return PyModule_Create(&myModule);
}

