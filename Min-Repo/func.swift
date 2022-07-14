import Metal
import MetalPerformanceShaders
import Accelerate
import Foundation

@_cdecl("metalswift_add")
public func addition(array1: UnsafeMutablePointer<Float>,array2: UnsafeMutablePointer<Float>, length: Int) -> UnsafeMutablePointer<Float> {

  var bFound = false
  var device : MTLDevice!
  device = MTLCreateSystemDefaultDevice()!
  let defaultLibrary = try! device.makeLibrary(filepath: "metal.metallib")
  let metalswift_addfunction = defaultLibrary.makeFunction(name: "metalswift_add")!
  let descriptor = MTLComputePipelineDescriptor()
  descriptor.computeFunction = metalswift_addfunction
  descriptor.supportIndirectCommandBuffers = true

  let computePipelineState = try! device.makeComputePipelineState(descriptor: descriptor, options: .init(), reflection: nil)
  var Ref1 : UnsafeMutablePointer<Float> = UnsafeMutablePointer(array1)
  var Ref2 : UnsafeMutablePointer<Float> = UnsafeMutablePointer(array2)
  var size = length
  let SizeBuffer : UnsafeMutableRawPointer = UnsafeMutableRawPointer(&size)

  let ll = MemoryLayout<Float>.stride * length

  var Buffer1:MTLBuffer! = device.makeBuffer(bytes:Ref1, length: ll, options:[])
  var Buffer2:MTLBuffer! = device.makeBuffer(bytes:Ref2, length: ll, options:[])
  var MetalBuffer:MTLBuffer! = device.makeBuffer(length: ll, options:[])
  let Size:MTLBuffer! = device.makeBuffer(bytes: SizeBuffer, length: MemoryLayout<Int>.size, options: [])

  var icbDescriptor:MTLIndirectCommandBufferDescriptor = MTLIndirectCommandBufferDescriptor()

  icbDescriptor.commandTypes.insert(MTLIndirectCommandType.concurrentDispatchThreads)
  icbDescriptor.inheritBuffers = false
  icbDescriptor.inheritPipelineState = false
  icbDescriptor.maxKernelBufferBindCount = 4


  var indirectCommandBuffer = device.makeIndirectCommandBuffer(descriptor: icbDescriptor, maxCommandCount: 1)!

  let icbCommand = indirectCommandBuffer.indirectComputeCommandAt(0)
  icbCommand.setComputePipelineState(computePipelineState)
  icbCommand.setKernelBuffer(Buffer1, offset: 0, at: 0)
  icbCommand.setKernelBuffer(Buffer2, offset: 0, at: 1)
  icbCommand.setKernelBuffer(MetalBuffer, offset: 0, at: 2)
  icbCommand.setKernelBuffer(Size, offset: 0, at: 3)
  icbCommand.concurrentDispatchThreads(MTLSize(width:computePipelineState.threadExecutionWidth, height: 1, depth: 1), threadsPerThreadgroup:MTLSize(width:computePipelineState.maxTotalThreadsPerThreadgroup, height: 1, depth: 1))
  print("wahoo")  
  for i in 0..<1000{
  print(i)
  let commandQueue = device.makeCommandQueue()!
  let commandBuffer = commandQueue.makeCommandBuffer()!
  let computeCommandEncoder = commandBuffer.makeComputeCommandEncoder()!
  computeCommandEncoder.executeCommandsInBuffer(indirectCommandBuffer, range:0..<1)
  computeCommandEncoder.endEncoding()
  commandBuffer.commit()
  commandBuffer.waitUntilCompleted()
  }
  return(MetalBuffer!.contents().assumingMemoryBound(to: Float.self))
}

