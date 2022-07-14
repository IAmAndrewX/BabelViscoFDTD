#include <metal_stdlib>
#include <metal_math>
using namespace metal;

#define size (*size_pr)
kernel void metalswift_add(const device float *Buffer1 [[ buffer(0) ]],
        const device float *Buffer2[[ buffer(1) ]],
        device float *MetalBuffer[[ buffer(2) ]],
        const device int *size_pr[[ buffer(3) ]],
        uint3 gid[[thread_position_in_grid]]) {
int i =  gid.x;
if (i<size)
{
        MetalBuffer[i]+= Buffer1[i] + Buffer2[i];
    }
}

kernel void metalswift_add2(const device float *Buffer1 [[ buffer(0) ]],
        const device float *Buffer2[[ buffer(1) ]],
        device float *MetalBuffer[[ buffer(2) ]],
        const device int *size_pr[[ buffer(3) ]],
        uint3 gid[[thread_position_in_grid]]) {
int i =  gid.x;
if (i<size)
{
        MetalBuffer[i]+= Buffer1[i] + Buffer2[i]*2;
    }
}