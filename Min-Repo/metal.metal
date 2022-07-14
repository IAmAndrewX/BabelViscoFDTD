#include <metal_stdlib>
#include <metal_math>
using namespace metal;

#define size (*size_pr)
kernel void metalswift_add(const device float *Buffer1 [[ buffer(0) ]],
const device float *Buffer2[[ buffer(1) ]],
device float *MetalBuffer[[ buffer(2) ]],
const device int *size_pr[[ buffer(3) ]]) {
    for (int i=0; i<size; i++){
        MetalBuffer[i] = Buffer1[i] + Buffer2[i];
    }
}